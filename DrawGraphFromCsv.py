import math
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
from dateutil import parser

tempArray = dict()
humArray = dict()
ratio_2065 = 1.0
nb_days = 7
#datemin = datetime.datetime.strptime('04/07/2019 09:00:00', '%d/%m/%Y %H:%M:%S')
#datemax = datetime.datetime.strptime('04/07/2019 12:00:00', '%d/%m/%Y %H:%M:%S')
datemax = datetime.datetime.now()
datemin = datetime.datetime.now()-datetime.timedelta(days=nb_days)




files = {}

def getRatio(temp, hum):
    tempArray = [-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]
    ratio30Array = [1.70748339855709, 1.62484595798505, 1.5841311591673, 1.49520500245845, 1.42515011213856,
                    1.30374014560648, 1.25149198213825, 1.17514837568155, 1.14909786488902, 1.11152678439235,
                    1.003738317757, 0.925298899086258, 0.866767137459764]
    ratio85Array = [1.25898214373842, 1.19730282530694, 1.17125999148222, 1.10119742419451, 1.05105019091887,
                    0.960029501490611, 0.922452023520767, 0.872306069739769, 0.852542995589399, 0.820211445627875,
                    0.737574005055831, 0.686380145167805, 0.642515230555794]
    ratio30 = ArrayInterpolation(temp, tempArray, ratio30Array)
    ratio85 = ArrayInterpolation(temp, tempArray, ratio85Array)
    ratio = Interpolation(hum, 30.0, 85.0, ratio30, ratio85)
    return ratio


def Interpolation(x, x1, x2, y1, y2):
    slope = (y2 - y1) / (x2 - x1)
    intercept = y2 - slope * x2
    return slope * x + intercept


def ArrayInterpolation(temp, tempArray, ratioArray):
    for i in range(0, len(tempArray) - 1):
        test = tempArray[i]
        if temp >= test:
            break
    y = Interpolation(temp, tempArray[i], tempArray[i + 1], ratioArray[i], ratioArray[i + 1])
    return y


def identityTemp(value, ratio, shift):
    return value

def identityHum(value, ratio, shift):
    return value

def identity(value, ratio, shift):
    return value


def identitywithShift(value, ratio, shift):
    return value - shift


def identitywithRatio(value, ratio, shift):
    return value / (ratio)


def identitywithRatioAndShift(value, ratio, shift):
    return (value - shift) * ratio_2065 / ratio

def delta(value, ratio,shift):
    return ((value/ratio)-value)

def analog(value, ratio, shift):
    return value / 1024 * 3.3


def rs(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    return Rs


def rsratio(value, ratio, shift):
    ratio = (1 - (1 / ratio))
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    return Rs + Rs * ratio * 10


def rsro(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = 1000.0 * (5.0 - sensor_volt) / sensor_volt
    rsro = Rs / (ratio * 1000)
    return rsro

def ratio(value, ratio, shift):
    return (ratio)


def diffAgainstRatioWithShift(value, ratio, shift):
    ret = 0.0
    if abs(value - shift) >= 1e-6:
        ret = ((((value - shift) - ((value - shift) / ratio))) / (value - shift)) * 100.0
    return ret



#def GetFiles(str):
#    if str not in files:
#        with open('Airpi_{0}.csv'.format(str)) as csvFile:
#            rows = csv.reader(csvFile)
#    return files[str]

def DrawCorelation(str, color, axe, function):
    x = list()
    y = list()
    with open('Airpi_{0}.csv'.format(str)) as csvFile:
        rows = csv.reader(csvFile)
        for row in rows:
            dt = parser.parse(row[0])
            if dt <= datemin or dt >= datemax:
                continue
            temp = float(row[2])
            hum = float(row[1])
            if function == 'Temp':
                y.append(float(temp))
            else:
                y.append(float(hum) )           
            x.append(math.log(float(row[3])))
    axe.spines['left'].set_color(color)
    axe.scatter(x, y, color=color, label='{0} - {1}'.format(str, function), s=1 )
    axe.yaxis.label.set_color(color)
    axe.set_ylabel(function)
    axe.tick_params('y', color=color)
    return
    

def Draw(str, color, axe, function=identity, linestyle='-'):
    shift = 9999.9
    x = list()
    y = list()
    _ratio = 1.0
    from dateutil import parser
    ref = datetime.datetime.now()-datetime.timedelta(days=nb_days)
    with open('Airpi_{0}.csv'.format(str)) as csvFile:
        rows = csv.reader(csvFile)
        for row in rows:
            #print('{0},{1},{2},{3}'.format(row[0], row[1], row[2],row[3]))
            temp = float(row[2])
            hum = float(row[1])
            _ratio = getRatio(temp, hum)
            dt = parser.parse(row[0])
            if dt <= datemin or dt >= datemax:
                continue
            x.append(dt)
            if function == identityTemp:
                input = temp
                str = 'Temperature'
            elif function == identityHum:
                input = hum
                str = 'Humidity'
            else:
                input = float(row[3])
            if input < shift:
                ratio_shift = _ratio
            shift = min(input, shift)
            value = function(input, _ratio, shift)
            y.append(value)
    axe.spines['left'].set_color(color)
    # axe = ax1.twinx()
    # axe.spines['right'].set_position(('axes', 1.0 + (index - 1) * 0.05))
    # axe.spines['right'].set_color(color)
    axe.plot(x, y, color=color, linewidth=0.5, linestyle=linestyle,
             label='{0} - {1}'.format(str, function.__name__) )
    axe.yaxis.label.set_color(color)
    axe.set_ylabel(str)
    axe.tick_params('y', color=color)
    return

def roCO2Calibration(value, ratio, shift):
    slope = -2.863140157
    intercept = 2.032692781
    sensor_volt = value / 1024 * 3.3
    rs = 1000.0 * (5.0 - sensor_volt) / sensor_volt

    #log10(ppm) = slope * log10(RS/R0) + intercept
    #log10(ppm) - intercept = log10(RS/R0) * slope
    #(log10(ppm)-intercept)/slope = log10(RS/R0)
    #pow10(((log10(ppm)-intercept)/slope ) = RS/R0
    #RO/RS = 1/(pow10(((log10(ppm)-intercept)/slope ))
    #R0 = RS/(pow10(((log10(ppm)-intercept)/slope ))

    # from library => ro = rs * pow((400/PARA), (1./PARB));
    # ro = rs / (math.pow(10,(math.log10(400) - intercept) / slope))
    ro = rs / (math.pow(10,(math.log10(400) - intercept) / slope))
    #PARA = 116.6020682
    #PARB = 2.769034857
    #ro = rs * math.pow((411/PARA), (1./PARB))
    return ro

def ppmMQ135CO2(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = 1000 * (5.0 - sensor_volt) / sensor_volt
    Ro = 8200
    RsRo = Rs / (Ro * ratio)
    slope = -2.863140157
    intercept = 2.032692781
    ppm = math.pow(10, slope * math.log10(RsRo) + intercept)
    #PARA = 116.6020682
    #PARB = 2.769034857
    #ppm = PARA * math.pow(RsRo,-PARB)
    return ppm


def ppmMQ7CO(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    Ro = 0.1705894968
    RsRo = Rs / (Ro * ratio)
    slope = -1.521938988
    intercept = 1.997866397
    ppm = math.pow(10, slope * math.log10(RsRo) + intercept)
    return ppm


def ppmMQ9CO(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    Ro = 0.7039850776
    RsRo = Rs / (Ro * ratio)
    slope = -2.218935344
    intercept = 2.767357919
    ppm = math.pow(10, slope * math.log10(RsRo) + intercept)
    return ppm


def ppmMQ135CO(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    Ro = 3.664298791
    RsRo = Rs / (Ro * ratio)
    slope = -3.958478627
    intercept = 2.780813909
    ppm = math.pow(10, slope * math.log10(RsRo) + intercept)
    return ppm

def dustConcentration(value,ratio, shift):
    c = (1.1 * value**3) - (3.8 * value**2) + (520 * value) + 0.62
    return c

print('-' * 80)

fig = plt.figure(figsize=(27, 17))
ax1 = plt.subplot2grid((4, 6), (0, 0), colspan = 4)
ax1.xaxis.set_minor_locator(mdates.HourLocator())
ax1.grid(which='major', color='#CCCCCC', linestyle='--')
ax1.grid(which='minor', color='#CCCCCC', linestyle=':')

ax12 = ax1.twinx()
ax12.spines['right'].set_position(('axes', 1.0))
ax12.spines['right'].set_color('g')
ax13 = ax1.twinx()
ax13.spines['right'].set_position(('axes', 1.04))
ax13.spines['right'].set_color('b')

ax2 = plt.subplot2grid((4, 6), (1, 0), sharex=ax1, rowspan=3, colspan=4)
ax2.xaxis.set_minor_locator(mdates.HourLocator())
ax2.grid(which='major', color='#CCCCCC', linestyle='--')
ax2.grid(which='minor', color='#CCCCCC', linestyle=':')

ax3 = plt.subplot2grid((4, 6), (0, 4), rowspan = 2, colspan = 2 )
ax3.grid(which='major', color='#CCCCCC', linestyle='--')
ax3.grid(which='minor', color='#CCCCCC', linestyle=':')

ax4 = plt.subplot2grid((4, 6), (2, 4), rowspan = 2, colspan = 2 )
ax4.grid(which='major', color='#CCCCCC', linestyle='--')
ax4.grid(which='minor', color='#CCCCCC', linestyle=':')

Draw('dust', 'y', ax1, identityTemp, '-')
Draw('dust', 'g', ax12, identityHum, '-')
Draw('dust', 'b', ax13, dustConcentration, '-')
#Draw('MQ135', 'b', ax13, ratio, '-')

Draw('MQ2','b', ax2         , ppmMQ135CO2,'-')
Draw('MQ135','r', ax2         , ppmMQ135CO2,'-')

DrawCorelation( 'MQ135', 'y', ax3, 'Temp')
DrawCorelation( 'MQ135', 'g', ax4, 'Hum')
#Draw('MQ2','b', ax2         , identitywithRatio,'-')
#Draw('MQ135','g', ax2         , identitywithRatio,'-')

#Draw('MQ2','r', ax2         , identity,'-')


#Draw('MQ135', 'y', ax1, identityTemp, '-')
#Draw('MQ135', 'g', ax12, identityHum, '-')
#Draw('MQ135', 'b', ax13, ratio, '-')
#Draw('PPD42NS', 'b', ax1, identity)

#Draw('MQ135','b', ax2         , identity,'-')
#Draw('MQ135','r', ax2         , identitywithRatio,'-')
#Draw('MQ135','g',ax2          , roCO2Calibration,'-')
#Draw('MQ135','r', ax2         , ppmMQ135CO2,':')

#Draw('MQ-135','b', ax2         , identity,'-')
#Draw('MQ-7'  ,'r', ax2        , identity,'-')
#Draw('MQ-9'  ,'m', ax2        , identity,'-')
#Draw('MQ-2'  ,'c', ax2        , identity,':')

# Draw('MQ-7', 'r', ax2, identitywithRatio)
# Draw('MQ-9', 'm', ax2, identitywithRatio)
# Draw('MQ-2', 'c', ax2, identitywithRatio)
# Draw('MQ-135', 'b', ax2, identitywithRatio)
# Draw('PPD42NS', 'r', ax2, identity,'--')

# Draw('MQ-135','b', ax2        , ppmMQ135CO2,'-')
# Draw('MQ-135','b', ax2       , ppmMQ135CO,'-')
# Draw('MQ-7','r', ax2         , ppmMQ7CO,'-')
# Draw('MQ-9','m', ax2         , ppmMQ9CO,'-')

ax1.legend(loc='upper center', shadow=True)
ax2.legend(loc='upper center', shadow=True)

fig.tight_layout()
ax1.yaxis.grid(True)
ax1.xaxis.grid(True)

ax2.yaxis.grid(True)
ax2.xaxis.grid(True)

#plt.subplots_adjust(right=0.92)
plt.show()

