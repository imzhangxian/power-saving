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
STORAGE_CAPACITY = 2
INITIAL_STORAGE = 0.8
STORAGE_ALERT_THRESHOLD = 0.5
STORAGE_SAFETY_LINE = 1

INTAKE_CEILING = 2
DTIME = 10 # dt - computational interval
PREDICTION_LEAD = 60 # prediction lead time (T)
PROCESSING_TIME = 60

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
def getMaxSpeed(demand, waterstore):
    speed = (STORAGE_CAPACITY - waterstore + demand)
    return speed if speed <= INTAKE_CEILING else INTAKE_CEILING

# min speed to keep the level over alert threshold in next prediction period
def getMinSpeed(demand, waterstore):
    deficit = (demand + STORAGE_SAFETY_LINE - waterstore)
    speed = deficit
    if speed < 0:
        speed = 0
    if speed > INTAKE_CEILING:
        speed = INTAKE_CEILING
    return speed

# electricity pricing at time t
def electricityPrice(t):
    hr = math.floor(t / 60)
    hr = hr if hr < 24 else hr -24
    return ELECTRICITY_PRICE[hr]

# speed adjustment algorithm
def adjustSpeed(t, demand, storedVol):
    eprice = electricityPrice(t)
    eprice_delta = electricityPrice(t + 60) - eprice
    demand_after_delay = predictDemand(t + PROCESSING_TIME)
    speed = getMaxSpeed(demand_after_delay, storedVol) if eprice_delta > 0 else getMinSpeed(demand_after_delay, storedVol)
    return speed

def simulateDemandSupply():
    print('simulate demand supply curve ... ')
    inventory = INITIAL_STORAGE
    intakes = []
    inventories = []
    dtimes = []
    eprices = []
    demands = []
    for t in range(DTIME, 60 * 24, DTIME):
        demand = predictDemand(t)
        intake = adjustSpeed(t, demand, inventory)
        # print('time at: ', math.floor(t/60), ':', t % 60, ', speed: ', 
        #        in_speed, ', volume: ', currentStorageVol)
        intakes.append(intake)
        inventories.append(inventory)
        dtimes.append(t/60)
        demands.append(demand)
        eprices.append(electricityPrice(t))
        # supply should be PROCESSING_TIME slower than intake
        k = math.floor((t - PROCESSING_TIME) / DTIME)
        supply = intakes[k if k > 0 else 0]
        inventory = inventory + (supply - demand) * DTIME / 60

    plt.plot(dtimes, intakes, label='Pump intake')
    plt.plot(dtimes, inventories, label='Inventory')
    plt.plot(dtimes, demands, label='Consumption')
    plt.plot(dtimes, eprices, label='Electricity price')
    plt.xlabel('Time 0-24')
    plt.ylabel('')
    plt.legend()
    plt.show()

simulateDemandSupply()

