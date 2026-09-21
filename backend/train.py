import os
from ultralytics import YOLO
from roboflow import Roboflow


def download_dataset():
    print("Downloading dataset from Open Images V7...")
    import fiftyone as fo
    import fiftyone.zoo as foz
    

    classes = [
        "Alarm clock", "Backpack", "Ball", "Bed", "Bench", "Bicycle", "Book", "Bottle", "Box", 
        "Briefcase", "Bus", "Car", "Ceiling fan", "Chair", "Clock", "Closet", "Clothing", 
        "Computer keyboard", "Computer monitor", "Computer mouse", "Couch", "Desk", "Digital clock", 
        "Door", "Drawer", "Drink", "Food", "Furniture", "Handbag", "Home appliance", "Humidifier", 
        "Kitchen appliance", "Kitchen knife", "Kitchen utensil", "Ladder", "Lamp", "Laptop", 
        "Light switch", "Luggage and bags", "Mobile phone", "Motorcycle", "Mouse", "Pen", "Person", 
        "Plant", "Refrigerator", "Remote control", "Shelf", "Sofa bed", "Stairs", "Stool", "Stop sign", 
        "Suitcase", "Swimming pool", "Table", "Tablet computer", "Taxi", "Telephone", "Television", 
        "Toilet", "Tool", "Train", "Vehicle", "Wall clock", "Wardrobe", "Washing machine", "Watch", 
        "Wheelchair", "Fruit", "Animal"
    ]

    export_dir = "custom_dataset"
    
    if not os.path.exists(export_dir):
        print("Fetching up to 10,000 images containing your classes...")
        dataset = foz.load_zoo_dataset(
            "open-images-v7",
            split="train",
            label_types=["detections"],
            classes=classes,
            max_samples=10000,
        )

        print("Exporting dataset to YOLO format...")
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.YOLOv5Dataset,
            label_field="ground_truth",
            split="train",
            classes=classes,
        )
        print("Dataset successfully exported to 'custom_dataset' directory.")
    else:
        print("Dataset already exists locally. Skipping download.")


    yaml_path = os.path.join(export_dir, "dataset.yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            content = f.read()
        if "val:" not in content:
            content += "val: .\\images\\train\\\n"
            with open(yaml_path, "w") as f:
                f.write(content)
                
    return export_dir


def train_model(data_path):
    print("Starting training...")
    model = YOLO("models/yolov8m.pt") 

    results = model.train(
        data=f"{data_path}/dataset.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        name="specs_custom_model", 
        device=0
    )
    
    print("Training complete! Model saved to 'runs/detect/specs_custom_model/weights/best.pt'")

if __name__ == "__main__":
    print("=== AI Vision Model Training ===")
    
    dataset_path = download_dataset()
    
    train_model(dataset_path)
