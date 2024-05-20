import pandas as pd
import plotly.express as px

# Load the data
# Load the data
rain = pd.read_csv(r'RTC\data\rain02.dat', delimiter=' ', header=None, names=['data', 'time', 'rain'])

# Combine 'data' and 'time' into a single column
rain['datetime'] = pd.to_datetime(rain['data'] + ' ' + rain['time'])

# Drop the original 'data' and 'time' columns
rain.drop(columns=['data', 'time'], inplace=True)

# Optional: Set the new 'datetime' column as the index
rain.set_index('datetime', inplace=True)
# Create the interactive plot with Plotly
fig = px.line(rain, title='Rain Data Over Time')

# Update layout for better visualization
fig.update_layout(
    width=1200,
    height=600,
    xaxis_title='Date',
    yaxis_title='Rainfall',
    font=dict(
        size=18
    )
)

# Show the plot
fig.show()
