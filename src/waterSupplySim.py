import numpy as np
import math
import matplotlib.pyplot as plt

#  units : 
#     volume - 10e+4 m3, 
#     time - minute (e.g. t=120 means 2:00AM)

# simplified demand curve on peak season (190k m3/day)
SIMPLE_DEMAND_PREDICTION = [0.262, 0.262, 0.262, 0.262, 0.262, 0.262, 0.931, 1.6, 1.6, 0.931, 
        0.262, 0.931, 1.6, 0.262, 0.262, 0.262, 0.262, 1.6, 1.6, 1.6, 1.6, 1.6, 0.262, 0.262]
ELECTRICITY_PRICE = [0.2695, 0.2695, 0.2695, 0.2695, 0.2695, 0.2695, 0.2695, 0.5615, 0.5615, 0.8366, 
        0.8366, 0.8366, 0.8366, 0.8366, 0.8366, 0.5615, 0.5615, 0.5615, 0.5615, 0.5615, 1.0107, 1.0107, 
        0.5615, 0.2695]
STORAGE_CAPACITY = 2 # max capacity of storage pools, currently 
INITIAL_STORAGE = 0.8
STORAGE_ALERT_THRESHOLD = 0.5
STORAGE_SAFETY_LINE = 0.6

INTAKE_CEILING = 2
DTIME = 10 # dt - computational interval
PREDICTION_LEAD = 60 # prediction lead time (T)
PROCESSING_TIME = 40 # water processing time

# predicted the water demand of (t, t + lead-time) based on demand curve
def predictDemand(t, duration = 60):
    PRED_SLICES = math.floor(duration / DTIME)
    d = 0
    for i in range(PRED_SLICES):
        hr = math.floor(t / 60)
        hr = hr if hr < 24 else hr -24
        d += SIMPLE_DEMAND_PREDICTION[hr] / PRED_SLICES
        t += DTIME
    return d

# max speed of next prediction period: strategy for valley price
def getMaxSpeed(demand, inventory):
    speed = (STORAGE_CAPACITY - inventory + demand)
    return speed if speed <= INTAKE_CEILING else INTAKE_CEILING

# min speed to keep the level over alert threshold in next prediction period
def getMinSpeed(demand, inventory):
    deficit = (demand - inventory + STORAGE_ALERT_THRESHOLD)
    speed = deficit
    if speed < 0:
        speed = 0
    if speed > INTAKE_CEILING:
        speed = INTAKE_CEILING
    return speed

# electricity pricing at time t
def electricityRate(t):
    hr = math.floor(t / 60)
    hr = hr if hr < 24 else hr -24
    return ELECTRICITY_PRICE[hr]

# speed adjustment algorithm:
#  - if 
def adjustSpeed(t, demand, supply, inventory):
    erate = electricityRate(t)
    erate_trend = 0
    for time_lapse in range(0, PREDICTION_LEAD + PROCESSING_TIME, DTIME):
        erate_trend = electricityRate(t + time_lapse) - erate
        if erate_trend != 0:
            break
    inventory_in_control = inventory - demand + supply # can only control supply after processing time
    demand_in_control = predictDemand(t + PROCESSING_TIME)
    maxspeed = getMaxSpeed(demand_in_control, inventory_in_control)
    minspeed = getMinSpeed(demand_in_control, inventory_in_control)
    speed = maxspeed if erate_trend > 0 else minspeed
    return speed

def simulateDemandSupply():
    print('simulate demand supply curve ... ')
    inventory = INITIAL_STORAGE
    intakes = []
    inventories = []
    dtimes = []
    erates = []
    demands = []
    for t in range(DTIME, 60 * 24, DTIME):
        demand = predictDemand(t)
        # supply should be PROCESSING_TIME slower than intake
        k = math.floor((t - PROCESSING_TIME) / DTIME)
        supply = intakes[k if k > 0 else 0] if intakes else demand
        intake = adjustSpeed(t, demand, supply, inventory)
        # print('time at: ', math.floor(t/60), ':', t % 60, ', speed: ', 
        #        in_speed, ', volume: ', currentStorageVol)
        intakes.append(intake)
        inventories.append(inventory)
        dtimes.append(t/60)
        demands.append(demand)
        erates.append(electricityRate(t))
        inventory = inventory + (supply - demand) * DTIME / 60
        if inventory > STORAGE_CAPACITY:
            print('Alert: !!!storage overflow!!!')
            inventory = STORAGE_CAPACITY

    plt.plot(dtimes, intakes, label='Pump intake')
    plt.plot(dtimes, inventories, label='Inventory')
    plt.plot(dtimes, demands, label='Consumption')
    plt.plot(dtimes, erates, label='Electricity price')
    plt.title('Power curves')
    plt.xlabel('Time 0-24')
    plt.ylabel('')
    plt.legend()
    plt.show()

simulateDemandSupply()

