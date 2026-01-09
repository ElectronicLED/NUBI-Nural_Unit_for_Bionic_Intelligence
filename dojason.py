import json

filename = "data.json"


# Combine them into one "wrapper" dictionary
# positions = {
#     "upper_body": 
#         {"default": [0, 0, 0, 0, 0, 0, 0], 
#          "fight0": [-45, 20, 110, 31, -20, -115, -3]
#          },

#     "lower_body": 
#         {
#         "default": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
#         "fight0": [0, 5, -50, -50, 0, 2, 0, 12, 40, 72, 6, -35]
#         }

# }
# 1. READ: Load the existing data into a variable
with open(filename, "r") as f:
    data = json.load(f)

print(data["upper_body"]["fight0"])
# data.update({"fight0": []})
# 2. EDIT: Modify the data (it's just a normal Python dictionary now)
# data["fruits"].append("orange")
# data["prices"].append(0.65)
# data["inventory"][0] = 95  # Updating the count for apples

# 3. SAVE: Write the updated dictionary back to the file
# data = positions
with open(filename, "w") as f:
    json.dump(data, f, indent=4)

print("File updated successfully!")