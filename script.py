import json
import os

def key_with_unities(key):
    key = key.replace(" ", "_")  # Replace spaces with underscores
    if key == "Age":
        return key.lower()
    elif key == "Weight":
        return f'{key}_kg'.lower()
    elif key == "High_Height":
        return f'{key}_cm'.lower()
    elif key == "Height":
        return f'{key}_cm'.lower()
    else:
        return key.lower()

if __name__ == '__main__':
    base_output_folder = "data"
    folder_path = "Medirisetest"

    os.makedirs(base_output_folder, exist_ok=True)

    counter = 1
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            numbered_folder = os.path.join(base_output_folder, str(counter))
            os.makedirs(numbered_folder, exist_ok=True)

            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            extracted_data = {"user_id": counter}  # Add user_id as an integer
            csv_data = []
            extracting_csv = False

            for i, line in enumerate(lines):
                line = line.strip()
                if extracting_csv:
                    parts = line.split("\t")
                    if len(parts) == 4:
                        csv_data.append(parts)
                elif ":" in line and i >= 2:  # Skip first two lines for JSON
                    key, value = map(str.strip, line.split(":", 1))
                    formatted_key = key_with_unities(key)
                    if formatted_key in ["user_id", "age", "weight_kg", "height_cm"]:
                        extracted_data[formatted_key] = int(value)
                    elif formatted_key in ["high_height_cm"]:
                        extracted_data[formatted_key] = float(value)
                    else:
                        extracted_data[formatted_key] = value
                if line.lower().startswith("high height"):
                    extracting_csv = True

            json_output_file = os.path.join(numbered_folder, "user_data.json")
            with open(json_output_file, 'w', encoding='utf-8') as json_file:
                json.dump(extracted_data, json_file, indent=4)
            print(f"Json saved to {json_output_file}")

            txt_output_file = os.path.join(numbered_folder, "accelerometer.txt")
            with open(txt_output_file, 'w', encoding='utf-8') as txtfile:
                txtfile.write("timestamp\tx\ty\tz\n")  # Header
                for row in csv_data:
                    txtfile.write("\t".join(row) + "\n")
                print(f"Txt saved to {txt_output_file}")

            counter += 1