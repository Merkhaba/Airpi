import math
import matplotlib.pyplot as plt

tempArray = dict()
humArray = dict()
ratio_2065 = 1.0


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
    # print('slope {0}'.format(slope))
    # print('intercept {0}'.format(intercept))
    return slope * x + intercept


def ArrayInterpolation(temp, tempArray, ratioArray):
    for i in range(0, len(tempArray) - 1):
        test = tempArray[i]
        if temp >= test:
            break
    y = Interpolation(temp, tempArray[i], tempArray[i + 1], ratioArray[i], ratioArray[i + 1])
    return y


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
    ro = rs / (math.pow(10,(math.log10(400) - intercept) / slope))
    return ro

def ratio(value, ratio, shift):
    return (ratio)


def diffAgainstRatioWithShift(value, ratio, shift):
    ret = 0.0
    if abs(value - shift) >= 1e-6:
        ret = ((((value - shift) - ((value - shift) / ratio))) / (value - shift)) * 100.0
    return ret


def Draw(str, color, axe, function=identity, linestyle='-'):
    shift = 9999
    ratio_shift = 1.0
    query = """select r.event_date,d.libelle,r.raw,d.comments
        from SensorDB.sensor_raw r,SensorDB.sensor_definition d
        where r.id_sensor = d.id_sensor
        and r.event_date > DATE_ADD(sysdate(),INTERVAL - 7 DAY)
        and d.libelle = '{0}'
        order by r.event_date desc, r.id_sensor desc"""
    cur.execute(query.format(str))
    rows = cur.fetchall()
    x = list()
    y = list()
    _ratio = 1.0
    _error_ratio = 0;
    for row in rows:
        if str == 'Temp':
            tempArray[row[0]] = row[2]
        elif str == 'Hum':
            humArray[row[0]] = row[2]
        else:
            try:
                temp = tempArray[row[0]]
                hum = humArray[row[0]]
                _ratio = getRatio(temp, hum)
            except KeyError:
                # do not set the new ratio
                _error_ratio += 1
                # print ("Temp or hum not found for {0}".format(row[0]))
        x.append(row[0])
        input = row[2]
        if input < shift:
            ratio_shift = _ratio
        shift = min(input, shift)
        value = function(input, _ratio, shift)
        y.append(value)
    print ('Ratio Errors {0} on {1}'.format(_error_ratio, str))
    axe.spines['left'].set_color(color)
    # axe = ax1.twinx()
    # axe.spines['right'].set_position(('axes', 1.0 + (index - 1) * 0.05))
    # axe.spines['right'].set_color(color)
    axe.plot(x, y, color=color, linewidth=0.5, linestyle=linestyle,
             label='{0} (min:{1:0.0f} ratio:{2:0.8f}) - {3}'.format(str, shift, ratio_shift, row[3]))
    axe.yaxis.label.set_color(color)
    axe.set_ylabel(str)
    axe.tick_params('y', color=color)
    return


def ppmMQ135CO2(value, ratio, shift):
    sensor_volt = value / 1024 * 3.3
    Rs = (5.0 - sensor_volt) / sensor_volt
    Ro = 1200
    RsRo = Rs / (Ro * ratio)
    slope = -2.863140157
    intercept = 2.032692781
    ppm = math.pow(10, slope * math.log10(RsRo) + intercept)
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


#db = MySQLdb.connect(host="192.168.0.50", user="sensor", passwd="NotAPW0!")
db = MySQLdb.connect(host="78.126.188.180", user="sensor", passwd="NotAPW0!")
cur = db.cursor()
print ('DB connection Successfull')
print('-' * 120)

fig = plt.figure(figsize=(17, 10))
ax1 = plt.subplot2grid((4, 1), (0, 0))
ax12 = ax1.twinx()
ax12.spines['right'].set_position(('axes', 1.0))
ax12.spines['right'].set_color('g')
ax13 = ax1.twinx()
ax13.spines['right'].set_position(('axes', 1.04))
ax13.spines['right'].set_color('b')
ax2 = plt.subplot2grid((4, 1), (1, 0), sharex=ax1, rowspan=3)

Draw('Temp', 'y', ax1, identity, '-')
Draw('Hum', 'g', ax12, identity, '-')
Draw('MQ-135', 'b', ax13, ratio, '-')
#Draw('PPD42NS', 'b', ax1, identity)

Draw('MQ-135','b', ax2         , identity,'-')
Draw('MQ-135','r', ax2         , identitywithRatio,'-')
Draw('MQ-135','g',ax2          , roCO2Calibration,'-')
#Draw('MQ-135','r', ax2         , ppmMQ135CO2,':')

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

plt.subplots_adjust(right=0.92)
plt.show()

cur.close()
db.close()
