import csv
import math
import h5py
import numpy
from pyhdf.SD import SD, SDC
import time

def load_bounding_box():
	print('reading county bounding box...')
	lines = []
	with open("data/ca_county.txt", "r") as f:
	    lines = f.readlines()
	
	ca_county = {}
	for line in lines:
		ind = line.find('(')
		ansi = line[:ind].strip()
		coords = []
		ind2 = line[ind:].find(')')
		ind2 += ind
		coords.append(line[ind:(ind2+1)])
		while ind2 + 2 < len(line):
			ind = line[ind2:].find('(')
			ind += ind2
			ind2 = line[ind:].find(')')
			ind2 += ind
			coords.append(line[ind:ind2+1])
		coord = []
		for c in coords:
			string = c[1:len(c)-1]
			box = string.split('; ')
			box[0] = box[0].split(', ')
			box[0][0] = float(box[0][0][:10])
			box[0][1] = float(box[0][1][:10])
			box[1] = box[1].split(', ')
			box[1][0] = float(box[1][0][:10])
			box[1][1] = float(box[1][1][:10])
			coord.append(box)
		ca_county[int(ansi)] = coord
	return ca_county

def load_tomato_prod_area():
	print('reading tomato production & farmland area data...')
	tomato1115 = []
	tomato1621 = []
	with open('data/tomato/tomato11-15.csv', newline='') as csvfile:
		temp = csv.reader(csvfile, delimiter=',', quotechar='|')
		for row in temp:
			tomato1115.append(row)
	with open('data/tomato/tomato16-21.csv', newline='') as csvfile:
		temp = csv.reader(csvfile, delimiter=',', quotechar='|')
		for row in temp:
			tomato1621.append(row)
	
	tomato_farmland = []
	tomato_production = []

	# read tomato11-15
	for i in range(1, len(tomato1115)):
		row = tomato1115[i]
		if row[0] == 'CENSUS':
			value = ''.join(row[20:-1])
			value = value[1:-1]
			if row[20].isnumeric():
				tomato_farmland.append([int(row[10]), int(row[20]), 2012])
			elif value.isnumeric():
				tomato_farmland.append([int(row[10]), int(value), 2012])
			else:
				tomato_farmland.append([int(row[10]), 0, 2012])
		else:
			value = ''.join(row[22:-1])
			value = value[1:-1]
			if value.isnumeric() and row[10].isnumeric():
				tomato_production.append([int(row[10]), int(value), int(row[1])])
			elif row[22].isnumeric() and row[10].isnumeric():
				tomato_production.append([int(row[10]), int(row[22]), int(row[1])])
			elif row[10].isnumeric():
				tomato_production.append([int(row[10]), value, int(row[1])])

	# read tomato16-21
	for i in range(1, len(tomato1621)):
		row = tomato1621[i]
		if row[0] == 'CENSUS':
			if int(row[1]) == 2017:
				value = ''.join(row[20:-1])
				value = value[1:-1]
				if row[20].isnumeric():
					tomato_farmland.append([int(row[10]), int(row[20]), 2017])
				elif value.isnumeric():
					tomato_farmland.append([int(row[10]), int(value), 2017])
				else:
					tomato_farmland.append([int(row[10]), 0, 2017])
		else:
			value = ''.join(row[23:-1])
			value = value[1:-1]
			if value.isnumeric() and row[10].isnumeric():
				tomato_production.append([int(row[10]), int(value), int(row[1])])
			elif row[23].isnumeric() and row[10].isnumeric():
				tomato_production.append([int(row[10]), int(row[23]), int(row[1])])
			elif row[10].isnumeric():
				tomato_production.append([int(row[10]), value, int(row[1])])

	return tomato_farmland, tomato_production

def get_latstart(lat):
	# lat start index
	temp = math.floor(lat * 100)
	while temp % 10 != 5:
		temp -= 1
	ind = (8995 - temp) / 10
	return int(ind+1), temp

def get_lonstart(lon):
	# lon start index
	temp = math.ceil(lon * 100)
	while temp % 10 != 5:
		temp += 1
	ind = (temp + 17995) / 10
	return int(ind+1), temp

def compute_LSTD(current_lst_day, ca_county_bbox):
	lstd = []
	for i in range(1, 116, 2):
		# loop over each county
		bbox_list = ca_county_bbox[i]
		count = 0
		tempsum = 0
		for bbox in bbox_list:
			# loop over each bbox
			latstarti, latstart = get_latstart(bbox[0][0])
			lonstarti, lonstart = get_lonstart(bbox[0][1])
			lati = latstarti
			lat = latstart
			loni = lonstarti
			lon = lonstart
			while lat > bbox[1][0] * 100:
				while lon < bbox[1][1] * 100:
					if current_lst_day[lati][loni] < 100:
						count += 1
						tempsum += current_lst_day[lati][loni]
					loni += 1
					lon += 10
				lati += 1
				lat -= 10
				loni = lonstarti
				lon = lonstart
		if count > 0:
			avg = tempsum / float(count)
		else:
			avg = 0
		lstd.append(avg)

	return lstd

def load_LSTD(ca_county_bbox):
	print('reading LST day files...')
	lst_day = []
	month = 6
	year = 2011
	lstd_year = []
	while year < 2022:
		print('  reading year ' + str(year) + ' month ' + str(month) + ' LSTD file...')
		filename = 'data/LST_day/MOD_LSTD_M_' + str(year) + '-0' + str(month) + '-01_rgb_3600x1800.SS.CSV'
		current_lst_day = []
		with open(filename, newline='') as csvfile:
		    lstdfile = csv.reader(csvfile, delimiter=' ', quotechar='|')
		    for row in lstdfile:
		    	row = row[0].split(',')
		    	temp = []
		    	for i in range(len(row)):
		    		r = row[i]
		    		if i > 0:
		    			r = round(float(r), 2)
		    		temp.append(r)
		    	current_lst_day.append(temp)

		# lstd for current month, year; format: [county ansi, avg]
		lstd_year.append(compute_LSTD(current_lst_day, ca_county_bbox))
		if month == 8:
			ansi = 1
			for i in range(len(lstd_year[0])):
				lst_day.append([ansi, lstd_year[0][i], lstd_year[1][i], lstd_year[2][i], year])
				ansi += 2
			month = 6
			year += 1
			lstd_year.clear()
		else:
			month += 1
	return lst_day

def compute_LSTN(current_lst_night, ca_county_bbox):
	lstn = []
	for i in range(1, 116, 2):
		# loop over each county
		bbox_list = ca_county_bbox[i]
		count = 0
		tempsum = 0
		for bbox in bbox_list:
			# loop over each bbox
			latstarti, latstart = get_latstart(bbox[0][0])
			lonstarti, lonstart = get_lonstart(bbox[0][1])
			lati = latstarti
			lat = latstart
			loni = lonstarti
			lon = lonstart
			while lat > bbox[1][0] * 100:
				while lon < bbox[1][1] * 100:
					if current_lst_night[lati][loni] < 100:
						count += 1.0
						tempsum += current_lst_night[lati][loni]
					loni += 1
					lon += 10
				lati += 1
				lat -= 10
				loni = lonstarti
				lon = lonstart
		if count > 0:
			avg = tempsum / float(count)
		else:
			avg = 0
		lstn.append(avg)

	return lstn

def load_LSTN(ca_county_bbox):
	print('reading LST night files...')
	lst_night = []
	month = 6
	year = 2011
	lstn_year = []
	while year < 2022:
		print('  reading year ' + str(year) + ' month ' + str(month) + ' LSTN file...')
		filename = 'data/LST_night/MOD_LSTN_M_' + str(year) + '-0' + str(month) + '-01_rgb_3600x1800.SS.CSV'
		current_lst_night = []
		with open(filename, newline='') as csvfile:
		    lstnfile = csv.reader(csvfile, delimiter=' ', quotechar='|')
		    for row in lstnfile:
		    	row = row[0].split(',')
		    	temp = []
		    	for i in range(len(row)):
		    		r = row[i]
		    		if i > 0:
		    			r = round(float(r), 2)
		    		temp.append(r)
		    	current_lst_night.append(temp)

		# lstn for current month, year; format: [county ansi, avg]
		lstn_year.append(compute_LSTD(current_lst_night, ca_county_bbox))
		if month == 8:
			ansi = 1
			for i in range(len(lstn_year[0])):
				lst_night.append([ansi, lstn_year[0][i], lstn_year[1][i], lstn_year[2][i], year])
				ansi += 2
			month = 6
			year += 1
			lstn_year.clear()
		else:
			month += 1
	return lst_night

def get_latstart_gpm(lat):
	temp = lat*1000 - 32625
	if temp <= 0:
		return 0, 32.625
	reti = int(temp // 250)
	if temp % 250 > 0:
		reti += 1
	return reti, 32.625 + 0.25*reti

def get_lonstart_gpm(lon):
	temp = lon*1000 + 124375
	if temp <= 0:
		return 0, -124.375
	reti = int(temp // 250)
	if temp % 250 > 0:
		reti += 1
	return reti, -124.375 + 0.25*reti

def compute_gpm(datalon, datalat, data, ca_county_bbox):
	gpm = []
	for i in range(1, 116, 2):
		# loop over each county
		bbox_list = ca_county_bbox[i]
		count = 0
		tempsum = 0
		for bbox in bbox_list:
			# loop over each bbox
			latstarti, latstart = get_latstart_gpm(bbox[1][0])
			lonstarti, lonstart = get_lonstart_gpm(bbox[0][1])
			lat = latstart
			lati = latstarti
			loni = lonstarti + 1
			lon = lonstart + 0.25
			count += 1
			tempsum += data[lonstarti, latstarti]
			while lat < bbox[0][0] :
				while lon < bbox[1][1]:
					count += 1.0
					tempsum += data[loni, lati]
					loni += 1
					lon += 0.25
				lati += 1
				lat += 0.25
				loni = lonstarti
				lon = lonstart
		if count > 0:
			avg = tempsum / float(count)
		else:
			avg = 0
		gpm.append(avg)

	return gpm

def load_gpm(ca_county_bbox):
	print('reading GPM files...')
	gpm = []
	month = 6
	year = 2011
	gpm_year = []
	while year < 2022:
		filename = 'data/GPM/3A-CLIM-MO-CS-124W42N114W32N.F18.SSMIS.GRID2021R1.' + str(year) + '0' + str(month) + '01-S000000-E235959.00000' + str(month) + '.V07A.HDF5'
		datalon = []
		datalat = []
		data = []
		with h5py.File(filename, "r") as f:
		    group = f['Grid']
		    datalon = list(group['lon'])
		    datalat = list(group['lat'])
		    data = group['surfacePrecipitation'][()]

		gpm_year.append(compute_gpm(datalon, datalat, data, ca_county_bbox))

		if month == 8:
			ansi = 1
			for i in range(len(gpm_year[0])):
				gpm.append([ansi, gpm_year[0][i], gpm_year[1][i], gpm_year[2][i], year])
				ansi += 2
			month = 6
			year += 1
			gpm_year.clear()
		else:
			month += 1
	return gpm

def compute_NDVI(current_ndvi, ca_county_bbox):
	ndvi = []
	for i in range(1, 116, 2):
		# loop over each county
		bbox_list = ca_county_bbox[i]
		count = 0
		tempsum = 0
		for bbox in bbox_list:
			# loop over each bbox
			latstarti, latstart = get_latstart(bbox[0][0])
			lonstarti, lonstart = get_lonstart(bbox[0][1])
			lati = latstarti
			lat = latstart
			loni = lonstarti
			lon = lonstart
			while lat > bbox[1][0] * 100:
				while lon < bbox[1][1] * 100:
					if current_ndvi[lati][loni] < 100:
						count += 1.0
						tempsum += current_ndvi[lati][loni]
					loni += 1
					lon += 10
				lati += 1
				lat -= 10
				loni = lonstarti
				lon = lonstart
		if count > 0:
			avg = tempsum / float(count)
		else:
			avg = 0
		ndvi.append(avg)

	return ndvi

def load_NDVI(ca_county_bbox):
	print('reading NDVI files...')
	ndvi = []
	month = 6
	year = 2011
	ndvi_year = []
	while year < 2022:
		print('  reading year ' + str(year) + ' month ' + str(month) + ' NDVI file...')
		filename = 'data/NDVI/MOD_NDVI_M_' + str(year) + '-0' + str(month) + '-01_rgb_3600x1800.SS.CSV'
		current_ndvi = []
		with open(filename, newline='') as csvfile:
		    ndvifile = csv.reader(csvfile, delimiter=' ', quotechar='|')
		    for row in ndvifile:
		    	row = row[0].split(',')
		    	temp = []
		    	for i in range(len(row)):
		    		r = row[i]
		    		if i > 0:
		    			r = round(float(r), 2)
		    		temp.append(r)
		    	current_ndvi.append(temp)

		# ndvi for current month, year; format: [county ansi, avg]
		ndvi_year.append(compute_NDVI(current_ndvi, ca_county_bbox))
		if month == 8:
			ansi = 1
			for i in range(len(ndvi_year[0])):
				ndvi.append([ansi, ndvi_year[0][i], ndvi_year[1][i], ndvi_year[2][i], year])
				ansi += 2
			month = 6
			year += 1
			ndvi_year.clear()
		else:
			month += 1
	return ndvi

def compute_ET(data_b, data_tl, data_tr, bottom_coor, top_l_coor, top_r_coor, ca_county_bbox):
	et = []
	clist = [1, 3, 5, 7, 9]
	for countyi in range(1, 116, 2):
		# loop over each county
		if countyi > clist[-1]:
			print('    finished computing county ', end='')
			for t in range(len(clist)):
				print(clist[t], end = ' ')
				clist[t] += 10
			print('ET data...')
		bbox_list = ca_county_bbox[countyi]
		count = 0
		tempsum = 0
		for box in bbox_list:
			starti, startj, endi, endj = 0, 0, 0, 0
			stop = 0
			verti_start = bottom_coor[2][0]
			hori_start_ = bottom_coor[2][1]
			verti_step = (bottom_coor[2][0] - bottom_coor[3][0]) / 2400
			hori_step = (bottom_coor[1][1] - bottom_coor[2][1]) / 2400
			hori_inc = bottom_coor[3][1] - bottom_coor[2][1]
			for i in range(2400):
				hori_start = hori_start_ + hori_inc * i / 2400
				for j in range(2400):
					lat = verti_start - i*verti_step
					lon = hori_start + j*hori_step
					if lat <= box[0][0] and lon >= box[0][1] and starti == 0 and startj == 0:
						starti = i
						startj = j
						stop += 1
					if lat < box[1][0] and lon > box[1][1] and endi == 0 and endj == 0:
						endi = i
						endj = j
						stop += 1
					if stop == 2:
						break
				if stop == 2:
					break
			if starti > endi:
				starti, endi = endi, starti
			if startj > endj:
				startj, endj = endj, startj

			for indi in range(starti, endi):
				for indj in range(startj, endj):
					if data_b[indi, indj] < 60000:
						tempsum += data_b[indi, indj]
						count += 1

			starti, startj, endi, endj = 0, 0, 0, 0
			stop = 0
			verti_start = top_l_coor[2][0]
			hori_start_ = top_l_coor[2][1]
			verti_step = (top_l_coor[2][0] - top_l_coor[3][0]) / 2400
			hori_step = (top_l_coor[1][1] - top_l_coor[2][1]) / 2400
			hori_inc = top_l_coor[3][1] - top_l_coor[2][1]
			for i in range(2400):
				hori_start = hori_start_ + hori_inc * i / 2400
				for j in range(2400):
					lat = verti_start - i*verti_step
					lon = hori_start + j*hori_step
					if lat <= box[0][0] and lon >= box[0][1] and starti == 0 and startj == 0:
						starti = i
						startj = j
						stop += 1
					if lat < box[1][0] and lon > box[1][1] and endi == 0 and endj == 0:
						endi = i
						endj = j
						stop += 1
					if stop == 2:
						break
				if stop == 2:
					break
			if starti > endi:
				starti, endi = endi, starti
			if startj > endj:
				startj, endj = endj, startj

			for indi in range(starti, endi):
				for indj in range(startj, endj):
					if data_tl[indi, indj] < 60000:
						tempsum += data_tl[indi, indj]
						count += 1

			starti, startj, endi, endj = 0, 0, 0, 0
			stop = 0
			verti_start = top_r_coor[2][0]
			hori_start_ = top_r_coor[2][1]
			verti_step = (top_r_coor[2][0] - top_r_coor[3][0]) / 2400
			hori_step = (top_r_coor[1][1] - top_r_coor[2][1]) / 2400
			hori_inc = top_r_coor[3][1] - top_r_coor[2][1]
			for i in range(2400):
				hori_start = hori_start_ + hori_inc * i / 2400
				for j in range(2400):
					lat = verti_start - i*verti_step
					lon = hori_start + j*hori_step
					if lat <= box[0][0] and lon >= box[0][1] and starti == 0 and startj == 0:
						starti = i
						startj = j
						stop += 1
					if lat < box[1][0] and lon > box[1][1] and endi == 0 and endj == 0:
						endi = i
						endj = j
						stop += 1
					if stop == 2:
						break
				if stop == 2:
					break
			if starti > endi:
				starti, endi = endi, starti
			if startj > endj:
				startj, endj = endj, startj

			for indi in range(starti, endi):
				for indj in range(startj, endj):
					if data_tr[indi, indj] < 60000:
						tempsum += data_tr[indi, indj]
						count += 1
		if count > 0:
			avg = tempsum / count
			et.append(avg)
		else:
			print('    no data found in county', countyi)
			et.append(0)
	return et

def load_ET(ca_county_bbox):
	print('reading ET files...')
	ET = []
	ET_year = []
	bottom_coor = []
	top_l_coor = []
	top_r_coor = []
	rows = []
	with open('data/ET/coords.txt', newline='') as coorfile:
		for row in coorfile:
			rows.append(row.split(' '))
	for i in range(1, 9, 2):
		bottom_coor.append([float(rows[0][i]), float(rows[0][i+1])])
		top_l_coor.append([float(rows[1][i]), float(rows[1][i+1])])
		top_r_coor.append([float(rows[2][i]), float(rows[2][i+1])])
	
	for year in range(2011, 2022):
		print('  reading year', year, 'ET file...')
		filename = 'data/ET/MOD16A3GF.A' + str(year) + '001.bottom.hdf'
		hdf = SD(filename, SDC.READ)
		
		DATAFIELD_NAME="ET_500m"
		data2D = hdf.select(DATAFIELD_NAME)
		data_b = data2D[:,:]

		filename = 'data/ET/MOD16A3GF.A' + str(year) + '001.top_l.hdf'
		hdf = SD(filename, SDC.READ)

		DATAFIELD_NAME="ET_500m"
		data2D = hdf.select(DATAFIELD_NAME)
		data_tl = data2D[:,:]

		filename = 'data/ET/MOD16A3GF.A' + str(year) + '001.top_r.hdf'
		hdf = SD(filename, SDC.READ)

		DATAFIELD_NAME="ET_500m"
		data2D = hdf.select(DATAFIELD_NAME)
		data_tr = data2D[:,:]
		
		ET_year = compute_ET(data_b, data_tl, data_tr, bottom_coor, top_l_coor, top_r_coor, ca_county_bbox)
		ind = 0
		for countyi in range(1, 116, 2):
			ET.append([countyi, ET_year[ind], year])
			ind += 1

	return ET


if __name__ == '__main__':
	t0 = time.time()
	# ca_county format: county ansi: list of bounding box
	# list of bounding box format: list of [upperleft[lat, lon], bottomright[lat, lon]]
	ca_county_bbox = load_bounding_box()

	# tomato_farmland format: list of [county ANSI, area, year]
	# tomato_production format: lsit of [county ANSI, production, year]
	tomato_farmland, tomato_production = load_tomato_prod_area()
	farmland = dict()
	production = dict()
	for t in tomato_farmland:
		farmland[(t[0], t[2])] = t[1]
	for t in tomato_production:
		production[(t[0], t[2])] = t[1]
	tomato_info = []
	count_valid = 0
	for y in range(2011, 2022):
		for ansi in range(1, 116, 2):
			year = 2012
			if y >= 2017:
				year = 2017
			if (ansi, year) in farmland and (ansi, y) in production:
				tomato_info.append([ansi, farmland[(ansi, year)], production[(ansi, y)], y])
				if farmland[(ansi, year)] > 0 and production[(ansi, y)] > 0:
					count_valid += 1
			else:
				tomato_info.append([ansi, 0, 0, y])
	
	# format: list of [county ansi, JUN avg, JUL avg, AUG avg, year]
	lstd = load_LSTD(ca_county_bbox)
	lstn = load_LSTN(ca_county_bbox)
	
	gpm = load_gpm(ca_county_bbox)

	ndvi = load_NDVI(ca_county_bbox)

	ET = load_ET(ca_county_bbox)

	# print('lstd size: ', len(lstd))
	# print('lstn size: ', len(lstn))
	# print('gpm size: ', len(gpm))
	# print('ndvi size: ', len(ndvi))

	# table structure (attribute names):
	# [county ansi, farmland area, production in tonnes, lstd_Jun, lstd_Jul, lstd_Aug, lstn_Jun, lstn_Jul, lstn_Aug
	# , gpm_Jun, gpm_Jul, gpm_Aug, ndvi_Jun, ndvi_Jul, ndvi_Aug, ET, year]
	# units: LSTD & LSTN: Celsius, GPM: mm/hour, NDVI: NA (index), ET: mm/year
	table = []
	for i in range(len(lstd)):
		table.append([lstd[i][0], tomato_info[i][1], tomato_info[i][2], lstd[i][1], lstd[i][2], lstd[i][3], lstn[i][1], lstn[i][2], lstn[i][3], gpm[i][1], gpm[i][2], gpm[i][3], ndvi[i][1]
			, ndvi[i][2], ndvi[i][3], ET[i][1], ET[i][2]])
	
	f = open('data/data.csv', 'w')
	f.write('CA_county_ansi,tomato_farmland_area(acres),tomato_production(tonnes),lstd_Jun,lstd_Jul,lstd_Aug,lstn_Jun,lstn_Jul,lstn_Aug,gpm_Jun,gpm_Jul,gpm_Aug,ndvi_Jun,ndvi_Jul,ndvi_Aug,ET,year')
	f.write('\n')
	for t in table:
		for i in range(len(t)):
			print("{:10}".format(round(t[i], 2)), end='')
			f.write(str(t[i]))
			if i < len(t)-1:
				f.write(',')
			else:
				f.write('\n')
		print()
	f.close()

	f = open('processed_data.csv', 'w')
	f.write('CA_county_ansi,tomato_farmland_area(acres),tomato_production(tonnes/acre),lstd_Jun,lstd_Jul,lstd_Aug,lstn_Jun,lstn_Jul,lstn_Aug,gpm_Jun,gpm_Jul,gpm_Aug,ndvi_Jun,ndvi_Jul,ndvi_Aug,ET,year\n')
	for t in table:
		if t[1] != 0 and t[2] != 0:
			f.write(str(t[0]) + ',' + str(t[1]) + ',')
			val = t[2] / t[1]
			f.write(str(val))
			for i in range(3, len(t)):
				f.write(',' + str(t[i]))
			f.write('\n')
	f.close()
	
	print('valid rows number:', count_valid)
	print('\nData processing time:', time.time() - t0, 'seconds')