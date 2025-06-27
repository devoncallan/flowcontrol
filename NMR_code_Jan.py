import zipfile as zf
import os
import shutil
import pandas as pd
import numpy as np
from scipy.integrate import simpson
import matplotlib.pyplot as plt

# Paths
zip_file = 'KJ-041-NMR.zip'  # Name of the zip file containing the data
input_folder = 'NMR-f'  # Folder where the zip content will be extracted
time_name_folder = 'NMR-time-name'  # Folder for renamed files with time-stamps
new_ref_folder = 'NMR-new-ref'  # Folder for frequency reference-adjusted files
int_folder = 'NMR-int'  # Folder for integrated results
final_csv_file = 'NMR-final.csv'  # Final output CSV file

# Step 1: Extract zip file
with zf.ZipFile(zip_file, 'r') as files:
    files.extractall(input_folder)  # Extract zip contents to input_folder

# Step 2: Create output directories
os.makedirs(time_name_folder, exist_ok=True)  # Create time_name_folder if it doesn't exist
os.makedirs(new_ref_folder, exist_ok=True)  # Create new_ref_folder if it doesn't exist
os.makedirs(int_folder, exist_ok=True)  # Create int_folder if it doesn't exist

# Step 3: Rename and move CSV files
for subdir in os.listdir(input_folder):  # Loop through extracted subdirectories
    subdir_path = os.path.join(input_folder, subdir)
    if os.path.isdir(subdir_path):  # Check if it's a directory
        time_stamp = subdir.split('-')[-1]  # Extract time-stamp from the folder name
        for file_name in os.listdir(subdir_path):  # Loop through files in the subdirectory
            if file_name.endswith('.csv'):  # Process only CSV files
                new_file_name = f'{time_stamp}.csv'  # Rename the file using the time-stamp
                source_file = os.path.join(subdir_path, file_name)  # Original file path
                destination_file = os.path.join(time_name_folder, new_file_name)  # New file path
                shutil.copyfile(source_file, destination_file)  # Copy file to time_name_folder

# Step 4: Process CSV files to adjust frequency reference
for file_name in os.listdir(time_name_folder):  # Loop through renamed files
    if file_name.endswith('.csv'):  # Process only CSV files
        file_path = os.path.join(time_name_folder, file_name)
        df = pd.read_csv(file_path)  # Read CSV file into a DataFrame
        
        # Find the first row where 'Intensity' exceeds 0.4 as the reference
        reference_row = df[df['Intensity'] > 0.4].iloc[0]
        reference_frequency = reference_row['Frequency(ppm)']  # Extract reference frequency
        
        # Subtract the reference frequency from all values in 'Frequency(ppm)'
        df['Frequency(ppm)'] -= reference_frequency
        
        # Save the adjusted file to the new_ref_folder
        output_file_path = os.path.join(new_ref_folder, file_name)
        df.to_csv(output_file_path, index=False)  # Write the adjusted DataFrame to CSV

# Step 5: Integrate data, calculate metrics with new constants n and s
x_range = (0, 1.300)  # Range for 'x' integration (0 to 1.300 ppm)
y_range = (0, 0.165)  # Range for 'y' integration (0 to 0.165 ppm)

for file_name in os.listdir(new_ref_folder):  # Loop through frequency-adjusted files
    if file_name.endswith('.csv'):  # Process only CSV files
        file_path = os.path.join(new_ref_folder, file_name)
        df = pd.read_csv(file_path)  # Read CSV file into a DataFrame
        
        # Select rows within x_range for integration
        df_x = df[(df['Frequency(ppm)'] >= x_range[0]) & (df['Frequency(ppm)'] <= x_range[1])]
        x = simpson(y=df_x['Intensity'], x=df_x['Frequency(ppm)'])  # Integrate for x range
        
        # Select rows within y_range for integration
        df_y = df[(df['Frequency(ppm)'] >= y_range[0]) & (df['Frequency(ppm)'] <= y_range[1])]
        y = simpson(y=df_y['Intensity'], x=df_y['Frequency(ppm)'])  # Integrate for y range
        
        # Calculate metrics: z, n, s, and Conversion
        z = y / x  # Calculate z as the ratio of y to x
        n = 4 * z  # Calculate n as 4 times z
        s = 1 - n  # Calculate s as 1 minus n
        conversion = s * 100  # Calculate conversion as s * 100
        
        # Store results in a new DataFrame
        result_df = pd.DataFrame({
            'x': [x],
            'y': [y],
            'k': [1],  # k is set to 1
            'z': [z],
            'n': [n],  # Add n to the CSV
            's': [s],  # Add s to the CSV
            'Conversion [%]': [conversion]  # Store Conversion value
        })
        
        # Save the results to a new CSV file in the int_folder
        output_file_path = os.path.join(int_folder, file_name)
        result_df.to_csv(output_file_path, index=False)  # Write results to CSV

# Step 6: Create final CSV and plot Conversion vs Time
files = [f for f in os.listdir(int_folder) if f.endswith('.csv')]  # List all CSV files in int_folder
files.sort()  # Sort files by their time-stamp (implicit in file name order)
time_points = []  # List to store time points
conversions = []  # List to store Conversion values
reference_time = None  # Variable to store the reference (initial) time

for file_name in files:  # Loop through each integrated result file
    time_str = file_name.split('.')[0]  # Extract the time-stamp from file name (without '.csv')
    hour = int(time_str[:2])  # Extract hour
    minute = int(time_str[2:4])  # Extract minute
    second = int(time_str[4:6])  # Extract second
    time_in_minutes = hour * 60 + minute + second / 60  # Convert time to minutes
    if reference_time is None:  # Set the first time point as the reference
        reference_time = time_in_minutes
    time_point = time_in_minutes - reference_time  # Calculate relative time
    file_path = os.path.join(int_folder, file_name)
    df = pd.read_csv(file_path)  # Read CSV file with conversion data
    conversion = df['Conversion [%]'].values[0]  # Extract Conversion value
    time_points.append(time_point)  # Add time point to list
    conversions.append(conversion)  # Add Conversion value to list

# Create a DataFrame for Time and Conversion
result_df = pd.DataFrame({
    'Time [min]': time_points,
    'Conversion [%]': conversions})
result_df.to_csv(final_csv_file, index=False)  # Save the final result to CSV

# Step 7: Plotting Conversion vs Time
plt.figure(figsize=(6.3, 3.5))  # Set plot size
plt.xlim(-2, 100)  # Set x-axis range
plt.ylim(-2, 102)  # Set y-axis range
plt.plot(result_df['Time [min]'], result_df['Conversion [%]'], marker='x', linestyle='None', color='#E69F00')  # Plot data
font_properties = {'family': 'Liberation Sans', 'size': 11}  # Set font properties
plt.xlabel('Time [min]', fontdict=font_properties)  # Label x-axis
plt.ylabel('Conversion [%]', fontdict=font_properties)  # Label y-axis
plt.tick_params(axis='both', which='major', labelsize=font_properties['size'])  # Set tick size
plt.grid(False)  # Remove grid
ax = plt.gca()  # Get current axis
ax.spines['top'].set_color('none')  # Hide top spine
ax.spines['right'].set_color('none')  # Hide right spine
plot_file_name = final_csv_file.replace('.csv', '_conversion_plot.png')  # Set plot file name
plt.savefig(plot_file_name, dpi=300, bbox_inches='tight')  # Save plot to file
plt.show()  # Display the plot
