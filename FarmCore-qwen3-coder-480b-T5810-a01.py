import asyncio
import csv
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Callable, Optional, Tuple

# Constants
FIELD_SIZE = 10
LOG_DIR = "logs"
DEFAULT_ANIMAL_CSV = "barn.csv"
DEFAULT_CROP_CSV = "farm.csv"

# Enums for states
class AnimalState(Enum):
    IDLE = "idle"
    GROWING = "growing"
    MATURE = "mature"

class CropState(Enum):
    EMPTY = "empty"
    PLANTED = "planted"
    READY = "ready"

# Dataclasses for templates and entities
@dataclass
class AnimalTemplate:
    animal: str
    minutes: int
    seconds: int
    product: str
    misc1: str
    misc2: str

@dataclass
class CropTemplate:
    crop: str
    minutes: int
    seconds: int
    misc1: str
    misc2: str
    misc3: str

@dataclass
class AnimalPool:
    template: AnimalTemplate
    count: int = 0
    state: AnimalState = AnimalState.IDLE
    maturity_time: Optional[datetime] = None

@dataclass
class CropPatch:
    template: Optional[CropTemplate] = None
    state: CropState = CropState.EMPTY
    maturity_time: Optional[datetime] = None

# Farm Core Class
class FarmCore:
    def __init__(self):
        self.animal_pools: Dict[str, AnimalPool] = {}
        self.field: List[List[CropPatch]] = [
            [CropPatch() for _ in range(FIELD_SIZE)] for _ in range(FIELD_SIZE)
        ]
        self.callbacks: List[Callable] = []
        
        # Setup logging
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        log_filename = f"{LOG_DIR}/FarmCoreLog-{timestamp}.log"
        
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize data
        self._load_animal_templates()
        self._load_crop_templates()
        self._initialize_animal_pools()

    def _create_default_csv(self, filename: str, headers: List[str], default_data: List[List[str]]):
        """Create default CSV files if they don't exist"""
        if not os.path.exists(filename):
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(default_data)

    def _load_animal_templates(self):
        """Load animal templates from barn.csv"""
        self._create_default_csv(
            DEFAULT_ANIMAL_CSV,
            ["animal", "minutes", "seconds", "product", "misc1", "misc2"],
            [
                ["cow", "0", "30", "milk", "", ""],
                ["chicken", "0", "20", "egg", "", ""],
                ["sheep", "0", "40", "wool", "", ""]
            ]
        )
        
        self.animal_templates: Dict[str, AnimalTemplate] = {}
        with open(DEFAULT_ANIMAL_CSV, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                template = AnimalTemplate(**row)
                self.animal_templates[template.animal] = template

    def _load_crop_templates(self):
        """Load crop templates from farm.csv"""
        self._create_default_csv(
            DEFAULT_CROP_CSV,
            ["crop", "minutes", "seconds", "misc1", "misc2", "misc3"],
            [
                ["wheat", "0", "25", "", "", ""],
                ["corn", "0", "35", "", "", ""],
                ["carrot", "0", "15", "", "", ""]
            ]
        )
        
        self.crop_templates: Dict[str, CropTemplate] = {}
        with open(DEFAULT_CROP_CSV, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                template = CropTemplate(**row)
                self.crop_templates[template.crop] = template

    def _initialize_animal_pools(self):
        """Initialize animal pools from templates"""
        for name, template in self.animal_templates.items():
            self.animal_pools[name] = AnimalPool(template=template)

    def register_callback(self, callback: Callable):
        """Register a callback for UI updates"""
        self.callbacks.append(callback)
        
    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                logging.error(f"Callback error: {e}")

    async def game_loop(self):
        """Main game loop that updates states periodically"""
        while True:
            await asyncio.sleep(1)  # Check every second
            now = datetime.now()
            
            # Update animal states
            for pool in self.animal_pools.values():
                if pool.state == AnimalState.GROWING and pool.maturity_time <= now:
                    pool.state = AnimalState.MATURE
                    logging.info(f"{pool.template.animal} pool is now mature")
                    
            # Update crop states
            for row in self.field:
                for patch in row:
                    if patch.state == CropState.PLANTED and patch.maturity_time <= now:
                        patch.state = CropState.READY
                        logging.info("A crop patch is now ready for harvest")
                        
            self._notify_callbacks()

    def feed_animals(self, animal_type: str, count: int) -> Dict[str, any]:
        """Feed animals to start growing process"""
        if animal_type not in self.animal_pools:
            return {"success": False, "message": f"Unknown animal type: {animal_type}"}
            
        pool = self.animal_pools[animal_type]
        if pool.state != AnimalState.IDLE:
            return {"success": False, "message": f"{animal_type} pool is not idle"}
            
        if count <= 0 or count > 6:
            return {"success": False, "message": "Count must be between 1 and 6"}
            
        pool.count = count
        duration = timedelta(
            minutes=pool.template.minutes,
            seconds=pool.template.seconds
        )
        pool.maturity_time = datetime.now() + duration
        pool.state = AnimalState.GROWING
        
        logging.info(f"Started feeding {count} {animal_type}(s)")
        self._notify_callbacks()
        return {"success": True, "message": f"Started feeding {count} {animal_type}(s)"}

    def harvest_animals(self, animal_type: str, count: int) -> Dict[str, any]:
        """Harvest mature animals"""
        if animal_type not in self.animal_pools:
            return {"success": False, "message": f"Unknown animal type: {animal_type}"}
            
        pool = self.animal_pools[animal_type]
        if pool.state != AnimalState.MATURE:
            return {"success": False, "message": f"{animal_type} pool is not mature"}
            
        if count <= 0 or count > pool.count:
            return {"success": False, "message": f"Invalid count. Pool has {pool.count} animals"}
            
        product = pool.template.product
        harvested_count = count
        pool.count -= count
        
        if pool.count == 0:
            pool.state = AnimalState.IDLE
            pool.maturity_time = None
            
        logging.info(f"Harvested {harvested_count} {product}(s) from {animal_type}")
        self._notify_callbacks()
        return {"success": True, "message": f"Harvested {harvested_count} {product}(s)"}

    def plant_crops(self, count: int, crop_type: str) -> Dict[str, any]:
        """Plant crops in available patches (pool-style)"""
        if crop_type not in self.crop_templates:
            return {"success": False, "message": f"Unknown crop type: {crop_type}"}
            
        if count <= 0:
            return {"success": False, "message": "Count must be positive"}
            
        template = self.crop_templates[crop_type]
        planted = 0
        
        # Find empty patches
        for row in self.field:
            for patch in row:
                if planted >= count:
                    break
                if patch.state == CropState.EMPTY:
                    duration = timedelta(
                        minutes=template.minutes,
                        seconds=template.seconds
                    )
                    patch.template = template
                    patch.maturity_time = datetime.now() + duration
                    patch.state = CropState.PLANTED
                    planted += 1
            if planted >= count:
                break
                
        if planted == 0:
            return {"success": False, "message": "No empty patches available"}
            
        logging.info(f"Planted {planted} {crop_type}(s)")
        self._notify_callbacks()
        return {"success": True, "message": f"Planted {planted} {crop_type}(s)"}

    def plant_crop(self, x: int, y: int, crop_type: str) -> Dict[str, any]:
        """Plant a crop at specific coordinates"""
        if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
            return {"success": False, "message": "Invalid coordinates"}
            
        if crop_type not in self.crop_templates:
            return {"success": False, "message": f"Unknown crop type: {crop_type}"}
            
        patch = self.field[y][x]
        if patch.state != CropState.EMPTY:
            return {"success": False, "message": "Patch is not empty"}
            
        template = self.crop_templates[crop_type]
        duration = timedelta(
            minutes=template.minutes,
            seconds=template.seconds
        )
        
        patch.template = template
        patch.maturity_time = datetime.now() + duration
        patch.state = CropState.PLANTED
        
        logging.info(f"Planted {crop_type} at ({x}, {y})")
        self._notify_callbacks()
        return {"success": True, "message": f"Planted {crop_type} at ({x}, {y})"}

    def harvest_crops(self, count: int) -> Dict[str, any]:
        """Harvest ready crops (pool-style)"""
        if count <= 0:
            return {"success": False, "message": "Count must be positive"}
            
        harvested = 0
        # Find ready patches
        for row in self.field:
            for patch in row:
                if harvested >= count:
                    break
                if patch.state == CropState.READY:
                    patch.state = CropState.EMPTY
                    patch.template = None
                    patch.maturity_time = None
                    harvested += 1
            if harvested >= count:
                break
                
        if harvested == 0:
            return {"success": False, "message": "No ready crops to harvest"}
            
        logging.info(f"Harvested {harvested} crop(s)")
        self._notify_callbacks()
        return {"success": True, "message": f"Harvested {harvested} crop(s)"}

    def harvest_crop(self, x: int, y: int) -> Dict[str, any]:
        """Harvest a specific crop patch"""
        if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
            return {"success": False, "message": "Invalid coordinates"}
            
        patch = self.field[y][x]
        if patch.state != CropState.READY:
            return {"success": False, "message": "Patch is not ready for harvest"}
            
        crop_type = patch.template.crop
        patch.state = CropState.EMPTY
        patch.template = None
        patch.maturity_time = None
        
        logging.info(f"Harvested {crop_type} from ({x}, {y})")
        self._notify_callbacks()
        return {"success": True, "message": f"Harvested {crop_type} from ({x}, {y})"}

    def get_animal_status(self) -> Dict[str, any]:
        """Get status of all animal pools"""
        status = {}
        for name, pool in self.animal_pools.items():
            status[name] = {
                "state": pool.state.value,
                "count": pool.count,
                "time_remaining": (
                    max(0, (pool.maturity_time - datetime.now()).total_seconds())
                    if pool.maturity_time else 0
                ) if pool.state == AnimalState.GROWING else 0
            }
        return status

    def get_crop_status(self) -> Dict[str, any]:
        """Get status of crop field"""
        empty = sum(1 for row in self.field for patch in row if patch.state == CropState.EMPTY)
        planted = sum(1 for row in self.field for patch in row if patch.state == CropState.PLANTED)
        ready = sum(1 for row in self.field for patch in row if patch.state == CropState.READY)
        
        return {
            "empty": empty,
            "planted": planted,
            "ready": ready,
            "field": [
                [self._get_patch_symbol(patch) for patch in row]
                for row in self.field
            ]
        }

    def _get_patch_symbol(self, patch: CropPatch) -> str:
        """Get symbol for a crop patch"""
        if patch.state == CropState.EMPTY:
            return "."
        elif patch.state == CropState.PLANTED:
            return f"({patch.template.crop[0].upper()})"
        else:  # READY
            return f"[{patch.template.crop[0].upper()}]"

    def get_config(self) -> Dict[str, any]:
        """Get available animals and crops"""
        return {
            "animals": list(self.animal_templates.keys()),
            "crops": list(self.crop_templates.keys())
        }

# CLI Interface
class FarmCLI:
    def __init__(self, farm: FarmCore):
        self.farm = farm

    def run(self):
        """Run the command-line interface"""
        print("Farm Management Simulator")
        print("Type 'help' for available commands\n")
        
        while True:
            try:
                command = input("> ").strip().split()
                if not command:
                    continue
                    
                cmd = command[0].lower()
                
                if cmd == "quit":
                    break
                elif cmd == "help":
                    self._show_help()
                elif cmd == "status":
                    self._show_status()
                elif cmd == "config":
                    self._show_config()
                elif cmd == "feed":
                    if len(command) != 3:
                        print("Usage: feed <animal_type> <count>")
                    else:
                        result = self.farm.feed_animals(command[1], int(command[2]))
                        print(result["message"])
                elif cmd == "harvest" and command[1] in self.farm.animal_pools:
                    if len(command) != 3:
                        print("Usage: harvest <animal_type> <count>")
                    else:
                        result = self.farm.harvest_animals(command[1], int(command[2]))
                        print(result["message"])
                elif cmd == "plant" and len(command) == 3:
                    result = self.farm.plant_crops(int(command[1]), command[2])
                    print(result["message"])
                elif cmd == "plant" and len(command) == 4:
                    result = self.farm.plant_crop(int(command[1]), int(command[2]), command[3])
                    print(result["message"])
                elif cmd == "harvest" and len(command) == 2:
                    result = self.farm.harvest_crops(int(command[1]))
                    print(result["message"])
                elif cmd == "harvest" and len(command) == 3:
                    result = self.farm.harvest_crop(int(command[1]), int(command[2]))
                    print(result["message"])
                else:
                    print("Unknown command. Type 'help' for available commands")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def _show_help(self):
        """Show help information"""
        print("""
Available Commands:
  feed <animal_type> <count>     - Feed animals to start production
  harvest <animal_type> <count>  - Harvest products from mature animals
  plant <count> <crop_type>      - Plant crops in any available patch
  plant <x> <y> <crop_type>      - Plant a crop at specific coordinates
  harvest <count>                - Harvest ready crops (anywhere)
  harvest <x> <y>                - Harvest a specific crop patch
  status                         - Show farm status
  config                         - Show available animals/crops
  help                           - Show this help message
  quit                           - Exit the game
        """)

    def _show_status(self):
        """Show farm status"""
        animal_status = self.farm.get_animal_status()
        crop_status = self.farm.get_crop_status()
        
        print("\n=== Animal Status ===")
        for animal, status in animal_status.items():
            time_info = f" ({status['time_remaining']:.0f}s remaining)" if status['time_remaining'] > 0 else ""
            print(f"{animal.capitalize()}: {status['state']} x{status['count']}{time_info}")
            
        print("\n=== Crop Status ===")
        print(f"Empty: {crop_status['empty']}, Planted: {crop_status['planted']}, Ready: {crop_status['ready']}")
        print("\nField Layout:")
        for row in crop_status["field"]:
            print(" ".join(row))
        print()

    def _show_config(self):
        """Show configuration"""
        config = self.farm.get_config()
        print(f"\nAvailable Animals: {', '.join(config['animals'])}")
        print(f"Available Crops: {', '.join(config['crops'])}\n")

# Main Execution
async def main():
    """Main entry point"""
    # Create farm instance
    farm = FarmCore()
    
    # Start game loop in background
    game_task = asyncio.create_task(farm._game_loop())
    
    # Run CLI
    cli = FarmCLI(farm)
    cli.run()
    
    # Cleanup
    game_task.cancel()
    try:
        await game_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())
