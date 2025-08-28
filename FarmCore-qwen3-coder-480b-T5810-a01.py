import asyncio
import csv
import os
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Callable, List, Tuple

#filename FarmCore-qwen3-coder-480b-T5810-a02.py

# Enums
class AnimalState(Enum):
    IDLE = "IDLE"
    GROWING = "GROWING"
    MATURE = "MATURE"

class CropState(Enum):
    EMPTY = "EMPTY"
    PLANTED = "PLANTED"
    READY = "READY"

# Dataclasses
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
class AnimalData:
    state: AnimalState
    timer: int  # in seconds
    template: AnimalTemplate

@dataclass
class CropData:
    state: CropState
    timer: int  # in seconds
    template: CropTemplate

# Farm Core Class
class FarmCore:
    def __init__(self):
        self.animals: Dict[str, List[AnimalData]] = {}
        self.crops: List[List[CropData]] = [[None for _ in range(10)] for _ in range(10)]
        self.field_grid: List[List[str]] = [['.' for _ in range(10)] for _ in range(10)]
        self.animal_templates: Dict[str, AnimalTemplate] = {}
        self.crop_templates: Dict[str, CropTemplate] = {}
        self.callbacks: List[Callable] = []
        
        # Setup logging
        self._setup_logging()
        
        # Load data
        self._load_animal_data()
        self._load_crop_data()
        
        # Initialize animals
        self._initialize_animals()

    def _setup_logging(self):
        """Setup logging to timestamped files"""
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_filename = f"logs/FarmCoreLog-{timestamp}.log"
        
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_animal_data(self):
        """Load animal templates from barn.csv"""
        if not os.path.exists("barn.csv"):
            self._create_default_barn_csv()
            
        try:
            with open("barn.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    template = AnimalTemplate(
                        animal=row["animal"],
                        minutes=int(row["minutes"]),
                        seconds=int(row["seconds"]),
                        product=row["product"],
                        misc1=row["misc1"],
                        misc2=row["misc2"]
                    )
                    self.animal_templates[row["animal"]] = template
            self.logger.info("Loaded animal data from barn.csv")
        except Exception as e:
            self.logger.error(f"Error loading animal data: {e}")

    def _load_crop_data(self):
        """Load crop templates from farm.csv"""
        if not os.path.exists("farm.csv"):
            self._create_default_farm_csv()
            
        try:
            with open("farm.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    template = CropTemplate(
                        crop=row["crop"],
                        minutes=int(row["minutes"]),
                        seconds=int(row["seconds"]),
                        misc1=row["misc1"],
                        misc2=row["misc2"],
                        misc3=row["misc3"]
                    )
                    self.crop_templates[row["crop"]] = template
            self.logger.info("Loaded crop data from farm.csv")
        except Exception as e:
            self.logger.error(f"Error loading crop data: {e}")

    def _create_default_barn_csv(self):
        """Create default barn.csv file"""
        with open("barn.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["animal", "minutes", "seconds", "product", "misc1", "misc2"])
            writer.writerow(["cow", 0, 30, "milk", "", ""])
            writer.writerow(["chicken", 0, 20, "egg", "", ""])
            writer.writerow(["sheep", 0, 40, "wool", "", ""])
        self.logger.info("Created default barn.csv")

    def _create_default_farm_csv(self):
        """Create default farm.csv file"""
        with open("farm.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["crop", "minutes", "seconds", "misc1", "misc2", "misc3"])
            writer.writerow(["wheat", 0, 25, "", "", ""])
            writer.writerow(["corn", 0, 35, "", "", ""])
            writer.writerow(["carrot", 0, 15, "", "", ""])
        self.logger.info("Created default farm.csv")

    def _initialize_animals(self):
        """Initialize animal pools"""
        for animal_type, template in self.animal_templates.items():
            self.animals[animal_type] = [
                AnimalData(state=AnimalState.IDLE, timer=0, template=template)
                for _ in range(6)
            ]
        self.logger.info("Initialized animal pools")

    async def game_loop(self):
        """Main game loop for updating states"""
        while True:
            await asyncio.sleep(1)  # Update every second
            self._update_animals()
            self._update_crops()
            self._notify_callbacks()

    def _update_animals(self):
        """Update animal timers and states"""
        for animal_list in self.animals.values():
            for animal in animal_list:
                if animal.state == AnimalState.GROWING:
                    animal.timer -= 1
                    if animal.timer <= 0:
                        animal.state = AnimalState.MATURE
                        animal.timer = 0

    def _update_crops(self):
        """Update crop timers and states"""
        for y in range(10):
            for x in range(10):
                crop = self.crops[y][x]
                if crop and crop.state == CropState.PLANTED:
                    crop.timer -= 1
                    if crop.timer <= 0:
                        crop.state = CropState.READY
                        crop.timer = 0
                        self.field_grid[y][x] = f"[{crop.template.crop[0].upper()}]"

    def _notify_callbacks(self):
        """Notify registered callbacks"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")

    def register_callback(self, callback: Callable):
        """Register a callback for updates"""
        self.callbacks.append(callback)

    # Animal Management Methods
    def feed_animals(self, animal_type: str, count: int) -> Dict[str, any]:
        """Feed animals to start growing"""
        if animal_type not in self.animals:
            return {"success": False, "message": f"Unknown animal type: {animal_type}"}
            
        fed_count = 0
        for animal in self.animals[animal_type]:
            if animal.state == AnimalState.IDLE and fed_count < count:
                template = animal.template
                animal.state = AnimalState.GROWING
                animal.timer = template.minutes * 60 + template.seconds
                fed_count += 1
                
        self.logger.info(f"Fed {fed_count} {animal_type}(s)")
        return {
            "success": True, 
            "message": f"Successfully fed {fed_count} {animal_type}(s)",
            "count": fed_count
        }

    def harvest_animals(self, animal_type: str, count: int) -> Dict[str, any]:
        """Harvest products from mature animals"""
        if animal_type not in self.animals:
            return {"success": False, "message": f"Unknown animal type: {animal_type}"}
            
        harvested_count = 0
        product = None
        for animal in self.animals[animal_type]:
            if animal.state == AnimalState.MATURE and harvested_count < count:
                product = animal.template.product
                animal.state = AnimalState.IDLE
                animal.timer = 0
                harvested_count += 1
                
        if harvested_count > 0:
            self.logger.info(f"Harvested {harvested_count} {product}(s) from {animal_type}(s)")
            return {
                "success": True,
                "message": f"Successfully harvested {harvested_count} {product}(s)",
                "product": product,
                "count": harvested_count
            }
        else:
            return {"success": False, "message": "No mature animals to harvest"}

    # Crop Management Methods
    def plant_crops(self, count: int, crop_type: str) -> Dict[str, any]:
        """Plant crops in available field patches"""
        if crop_type not in self.crop_templates:
            return {"success": False, "message": f"Unknown crop type: {crop_type}"}
            
        planted_count = 0
        template = self.crop_templates[crop_type]
        
        for y in range(10):
            for x in range(10):
                if planted_count >= count:
                    break
                if self.crops[y][x] is None:
                    timer = template.minutes * 60 + template.seconds
                    self.crops[y][x] = CropData(
                        state=CropState.PLANTED,
                        timer=timer,
                        template=template
                    )
                    self.field_grid[y][x] = f"({crop_type[0].upper()})"
                    planted_count += 1
            if planted_count >= count:
                break
                
        self.logger.info(f"Planted {planted_count} {crop_type}(s)")
        return {
            "success": True,
            "message": f"Successfully planted {planted_count} {crop_type}(s)",
            "count": planted_count
        }

    def plant_crop(self, x: int, y: int, crop_type: str) -> Dict[str, any]:
        """Plant a crop at specific coordinates"""
        if not (0 <= x < 10 and 0 <= y < 10):
            return {"success": False, "message": "Invalid coordinates"}
            
        if crop_type not in self.crop_templates:
            return {"success": False, "message": f"Unknown crop type: {crop_type}"}
            
        if self.crops[y][x] is not None:
            return {"success": False, "message": "Patch already occupied"}
            
        template = self.crop_templates[crop_type]
        timer = template.minutes * 60 + template.seconds
        self.crops[y][x] = CropData(
            state=CropState.PLANTED,
            timer=timer,
            template=template
        )
        self.field_grid[y][x] = f"({crop_type[0].upper()})"
        
        self.logger.info(f"Planted {crop_type} at ({x}, {y})")
        return {
            "success": True,
            "message": f"Successfully planted {crop_type} at ({x}, {y})"
        }

    def harvest_crops(self, count: int) -> Dict[str, any]:
        """Harvest ready crops (pool style)"""
        harvested = []
        harvested_count = 0
        
        for y in range(10):
            for x in range(10):
                if harvested_count >= count:
                    break
                crop = self.crops[y][x]
                if crop and crop.state == CropState.READY:
                    harvested.append(crop.template.crop)
                    self.crops[y][x] = None
                    self.field_grid[y][x] = "."
                    harvested_count += 1
            if harvested_count >= count:
                break
                
        if harvested_count > 0:
            self.logger.info(f"Harvested {harvested_count} crop(s)")
            return {
                "success": True,
                "message": f"Successfully harvested {harvested_count} crop(s)",
                "crops": harvested,
                "count": harvested_count
            }
        else:
            return {"success": False, "message": "No ready crops to harvest"}

    def harvest_crop(self, x: int, y: int) -> Dict[str, any]:
        """Harvest a crop at specific coordinates"""
        if not (0 <= x < 10 and 0 <= y < 10):
            return {"success": False, "message": "Invalid coordinates"}
            
        crop = self.crops[y][x]
        if not crop:
            return {"success": False, "message": "No crop at this location"}
            
        if crop.state != CropState.READY:
            return {"success": False, "message": "Crop is not ready for harvest"}
            
        crop_type = crop.template.crop
        self.crops[y][x] = None
        self.field_grid[y][x] = "."
        
        self.logger.info(f"Harvested {crop_type} at ({x}, {y})")
        return {
            "success": True,
            "message": f"Successfully harvested {crop_type} at ({x}, {y})",
            "crop": crop_type
        }

    # Query Methods
    def get_animal_status(self) -> Dict[str, any]:
        """Get status of all animals"""
        status = {}
        for animal_type, animals in self.animals.items():
            idle = sum(1 for a in animals if a.state == AnimalState.IDLE)
            growing = sum(1 for a in animals if a.state == AnimalState.GROWING)
            mature = sum(1 for a in animals if a.state == AnimalState.MATURE)
            status[animal_type] = {
                "idle": idle,
                "growing": growing,
                "mature": mature
            }
        return status

    def get_crop_status(self) -> Dict[str, any]:
        """Get status of all crops"""
        empty = sum(1 for row in self.crops for patch in row if patch is None)
        planted = sum(1 for row in self.crops for patch in row if patch and patch.state == CropState.PLANTED)
        ready = sum(1 for row in self.crops for patch in row if patch and patch.state == CropState.READY)
        
        return {
            "empty": empty,
            "planted": planted,
            "ready": ready
        }

    def get_field_visualization(self) -> str:
        """Get field visualization with consistent cell spacing"""
        result = "  0  1  2  3  4  5  6  7  8  9 \n"
        for y in range(10):
            row = f"{y} "
            for x in range(10):
                if self.crops[y][x] is None:
                    row += "[ ] "  # Empty patch with consistent spacing
                else:
                    crop = self.crops[y][x]
                    symbol = crop.template.crop[0].upper()
                    if crop.state == CropState.PLANTED:
                        row += f"({symbol}) "  # Planted crops in parentheses
                    else:  # READY
                        row += f"[{symbol}] "   # Ready crops in brackets
            result += row + "\n"
        return result


    def get_available_animals(self) -> list:
        """Get list of available animal types"""
        return list(self.animal_templates.keys())

    def get_available_crops(self) -> list:
        """Get list of available crop types"""
        return list(self.crop_templates.keys())


# CLI Interface for Testing
class FarmCLI:
    def __init__(self, farm: FarmCore):
        self.farm = farm

    def run(self):
        """Run the CLI interface"""
        print("Farm Management Simulation")
        print("Type 'help' for available commands")
        
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
                elif cmd == "feed":
                    if len(command) >= 3:
                        animal_type = command[1]
                        count = int(command[2])
                        result = self.farm.feed_animals(animal_type, count)
                        print(result["message"])
                    else:
                        print("Usage: feed <animal_type> <count>")
                elif cmd == "harvest" and len(command) >= 2:
                    if command[1].isdigit():  # Harvest crops by count
                        count = int(command[1])
                        result = self.farm.harvest_crops(count)
                        print(result["message"])
                    elif len(command) >= 3:  # Harvest animal or crop at coordinates
                        try:
                            x, y = int(command[1]), int(command[2])
                            result = self.farm.harvest_crop(x, y)
                            print(result["message"])
                        except ValueError:
                            animal_type = command[1]
                            count = int(command[2])
                            result = self.farm.harvest_animals(animal_type, count)
                            print(result["message"])
                    else:
                        print("Usage: harvest <count> OR harvest <animal_type> <count> OR harvest <x> <y>")
                elif cmd == "plant":
                    if len(command) >= 3 and command[1].isdigit() and command[2].isdigit():
                        x, y = int(command[1]), int(command[2])
                        crop_type = command[3] if len(command) > 3 else "wheat"
                        result = self.farm.plant_crop(x, y, crop_type)
                        print(result["message"])
                    elif len(command) >= 3:
                        count = int(command[1])
                        crop_type = command[2]
                        result = self.farm.plant_crops(count, crop_type)
                        print(result["message"])
                    else:
                        print("Usage: plant <count> <crop_type> OR plant <x> <y> [crop_type]")
                elif cmd == "status":
                    self._show_status()
                elif cmd == "field":
                    print(self.farm.get_field_visualization())
                elif cmd == "config":
                    self._show_config()
                else:
                    print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def _show_help(self):
        """Show help information"""
        print("\nAvailable Commands:")
        print("  feed <animal_type> <count>     - Feed animals")
        print("  harvest <animal_type> <count>  - Harvest animal products")
        print("  harvest <count>                - Harvest ready crops (pool style)")
        print("  harvest <x> <y>                - Harvest crop at coordinates")
        print("  plant <count> <crop_type>      - Plant crops (auto-assign)")
        print("  plant <x> <y> [crop_type]      - Plant crop at coordinates")
        print("  status                         - Show farm status")
        print("  field                          - Show field visualization")
        print("  config                         - Show available animals/crops")
        print("  help                           - Show this help")
        print("  quit                           - Exit the game")
        print()

    def _show_status(self):
        """Show farm status"""
        print("\nAnimal Status:")
        animal_status = self.farm.get_animal_status()
        for animal_type, status in animal_status.items():
            print(f"  {animal_type}: Idle={status['idle']}, Growing={status['growing']}, Mature={status['mature']}")
        
        print("\nCrop Status:")
        crop_status = self.farm.get_crop_status()
        print(f"  Empty: {crop_status['empty']}, Planted: {crop_status['planted']}, Ready: {crop_status['ready']}")
        print()

    def _show_config(self):
        """Show configuration"""
        print("\nAvailable Animals:")
        for animal in self.farm.get_available_animals():
            print(f"  {animal}")
        
        print("\nAvailable Crops:")
        for crop in self.farm.get_available_crops():
            print(f"  {crop}")
        print()


# Main Execution
async def main():
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Initialize farm system
    farm = FarmCore()
    
    # Start the game loop in the background
    game_task = asyncio.create_task(farm.game_loop())
    
    # Run CLI interface
    cli = FarmCLI(farm)
    try:
        cli.run()
    finally:
        # Cancel the game loop when done
        game_task.cancel()
        try:
            await game_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
