import numpy as np
import pandas as pd

#  Parameters
RefN = 90
RefE = 0

def PivotTableCount(ndirections, vwinds, speed, dir, direction):

    N = np.linspace(0, 360, ndirections + 1)[:-1]
    n = 180 / ndirections

    count = np.zeros((len(N), len(vwinds)))

    for i in range(len(N)):
        d1 = np.mod((N[i] - n), 360)
        d2 = N[i] + n

        if d1 > d2:
            cond = (dir >= d1) | (dir < d2)
        else:
            cond = (dir >= d1) & (dir < d2)

        # Calculate histogram counts of speed within specified wind speed bins
        counter, _ = np.histogram(speed[cond], bins=np.append(vwinds, np.inf))
        # Cumulative counts for each wind speed bin
        count[i, :] = np.cumsum(counter[:len(vwinds)])

    # Convert to percentage of total elements

    return count / len(direction) * 100

def CountTable(ndirections, vwinds, speed, dir, direction):
    N = np.linspace(0, 360, ndirections + 1)[:-1]
    n = 180 / ndirections


    # Convert to percentage of total elements
    count = PivotTableCount(ndirections, vwinds, speed, dir, direction)

    # Convert count to frequency per single direction and speed
    count = np.hstack((count[:, [0]], np.diff(count, axis=1)))
    column_names = [f'[{vwinds[i]}, {vwinds[i+1]})' for i in range(len(vwinds) - 1)] + [f'[{vwinds[-1]}, Inf)']
    count_df = pd.DataFrame(count, columns=column_names)

    directions = np.mod(RefN - N / 90 * (RefN - RefE), 360)

    # Create wind direction intervals and insert them into the first column
    wdirs = [f"[{np.mod((i - n), 360):.2f} , {(i + n):.2f})" for i in directions]
    count_df.insert(0, 'Direction Interval (°)', wdirs)

    # Insert average directions as the second column
    count_df.insert(1, 'Avg. Direction', directions)

    # Sort count_df by average directions
    count_df = count_df.sort_values(by='Avg. Direction')

    # Calculate WindZeroFrequency
    WindZeroFrequency = 100 - np.sum(count)
    # Convert to percentage of total WindZeroFrequency
    WindZeroFrequency = WindZeroFrequency * (WindZeroFrequency / 100 > np.finfo(float).eps)

    # Add WindZeroFrequency row to the DataFrame
    count_df.loc['No Direction'] = ['[0 , 360)', 'Wind Speed = 0'] + [''] * (count_df.shape[1] - 3) + [str(WindZeroFrequency)]

    # Calculate the total for each row and add it as a new column
    count_df['total'] = count_df.iloc[:, 2:].sum(axis=1)
    count_df.loc['Total'] =  count_df.iloc[:16,2: ].sum(axis=0)

    return count_df

# Function to process the data and save the table
def ProcessTable(ndirections, vwinds,season_df, filename):

# Define and Convert wind speed and wind direction into a column vector
    speed = season_df['speed'].to_numpy().reshape(-1, 1)
    direction = season_df['direction'].to_numpy().reshape(-1, 1)

# Ensure that the direction is between 0 and 360º
    dir = np.mod((RefN - direction) / (RefN - RefE) * 90, 360)

# Wind = 0 does not have direction, so it cannot appear in a wind rose
    dir = dir[speed.flatten() > 0]
    speed = speed[speed.flatten() > 0]

    if len(vwinds) > 0 and vwinds[0] != 0:
        vwinds = np.insert(vwinds, 0, 0)

    count_df = CountTable(ndirections, vwinds, speed, dir, direction)

    if 99.9999 <= count_df.iloc[-1, -1] < 100.0001:
        # print(f"{filename} ok")
        table = count_df.drop(index=['No Direction', 'Total'], columns=['total'])
        table.to_csv(f'Tables\\{filename}.csv', index=False)
    else:
        print(f'{filename} total is not 100%')
    # return table