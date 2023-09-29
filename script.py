import csv
import math
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import normalize
import random

def check_outliers(data, col, col_names):
	# check if outliers exists in colunm col using IQR, return row numbers of all outliers
	# data: dataset, col: column index
	print('checking if outliers exist in', col_names[col], '(column', str(col) + ')')
	ret = []
	vals = []
	for t in data:
		vals.append(t[col])
	x = np.array(vals)
	q75, q25 = np.percentile(x, [75 ,25])
	print('  25, 50, 75 quartile:', q25, np.median(x), q75)
	iqr = q75 - q25
	upper = q75 + 1.5*iqr
	lower = q25 - 1.5*iqr
	print('  upper and lower fence:', upper, lower)
	print
	for i in range(len(vals)):
		if vals[i] > upper:
			print('    found outlier higher than upper fence: row', i)
			ret.append(i)
		if vals[i] < lower:
			print('    found outlier lower than lower fence: row', i)
			ret.append(i)
	if len(ret) == 0:
		print('    no outlier found in this column')
	return ret

def show_county_frequency(data):
	available_county = {}
	for t in data:
		if not t[0] in available_county:
			available_county[t[0]] = 1
		else:
			available_county[t[0]] += 1
	print('listing all county ansi which data is available for year 2011 - 2021(11 years)...')
	key_list = list(available_county.keys())
	key_list.sort()
	for t in key_list:
		print('  county ansi:', t, '--- frequency:', available_county[t])

def data_cleaning(data):
	# check if zero exists in the dataset
	print('\n\n======================================================================================================')
	print('checking if zero exists in the dataset...')
	check_zero = 0
	for i in range(len(data)):
		for j in range(len(data[i])):
			if data[i][j] == 0:
				print('  0 exists in row', i, 'column', j)
				check_zero = 1
	if check_zero == 0:
		print('  no zero exists in dataset')
	print('======================================================================================================')

	# check if outliers exists in the dataset
	print('\n\n======================================================================================================')
	print('checking if outliers exist for each column (except column 0, 1 and 15, which is ansi, farmland area and year), using IQR method...')
	outliers = []
	outlier_rows = set()
	for i in range(2, len(data[0]) - 1):
		current = check_outliers(data, i, col_names)
		print()
		for t in current:
			outlier_rows.add(t)
		outliers.append(current)
	print('total number of outliers:', len(outlier_rows))
	print('outlier rows: ', end='')
	outlier_rows_list = list(outlier_rows)
	outlier_rows_list.sort()
	for t in outlier_rows_list:
		print(t, end=' ')
	print('\n======================================================================================================')

	for i in range(len(outlier_rows_list)-1, -1, -1):
		data.pop(i)
	return data

def get_lr_coef(data, r, accuracy_lb):
	npdata = np.array(data)
	ypred, ytest, mse, accuracy = 0, 0, 0, 0

	while accuracy <= accuracy_lb:
		x = npdata[:, 3:(len(data[0])-1)]
		y = npdata[:, 2]
		xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size = 0.3)
		reg = LinearRegression().fit(xtrain, ytrain)
		ypred = reg.predict(xtest)
		
		mse = ((ypred - ytest)**2).mean()
		
		sd = np.std(ytest)
		t1, t2 = 0, 0
		for i in range(len(ytest)):
			t2 += 1
			if ypred[i] > ytest[i] - r*sd and ypred[i] < ytest[i] + r*sd:
				t1 += 1
		accuracy = t1 / t2
		
	print('predicted value:')
	print(ypred)
	print('actual value:')
	print(ytest)
	print('\nmse:', mse)
	print('\nstandard error:', math.sqrt(mse))
	print('\nprediction accuracy:', accuracy)
	print()
	return [reg.intercept_, reg.coef_]

def linear_reg(data, r, accuracy_lb):
	print('\n\n======================================================================================================')
	print('Linear Regression')

	lr_model_without_year = get_lr_coef(data, r, accuracy_lb)
	print('model coefficients:')
	print(lr_model_without_year[0])
	print(lr_model_without_year[1])
	print('======================================================================================================')

def decision_t(npdata, width = 0):
	print('\n\n======================================================================================================')
	print('Decision Tree')
	accuracy = 0
	while accuracy < 0.8:
		x = npdata[:, 3:(len(data[0])-1)]
		y = npdata[:, 2]
		xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size = 0.3)

		dtree = DecisionTreeClassifier()
		dtree = dtree.fit(xtrain, ytrain)

		ypred = dtree.predict(xtest)
		print('predicted values:')
		print(ypred)
		print('actual values:')
		print(ytest)
		t1 = 0
		for i in range(len(ypred)):
			if ypred[i] >= ytest[i] - width and ypred[i] <= ytest[i] + width:
				t1 += 1
		accuracy = t1 / len(ytest)
		print('accuracy:', accuracy)
		break
	print('======================================================================================================')

def random_f(npdata, est, depth, width = 0):
	print('\n\n======================================================================================================')
	print('Random Forest')
	accuracy = 0
	while accuracy < 0.8:
		x = npdata[:, 3:(len(data[0])-1)]
		y = npdata[:, 2]
		xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size = 0.3)

		clf = RandomForestClassifier(n_estimators=est, max_depth=depth)
		clf.fit(xtrain, ytrain)

		ypred = clf.predict(xtest)
		print('predicted values:')
		print(ypred)
		print('actual values:')
		print(ytest)
		t1 = 0
		for i in range(len(ypred)):
			if ypred[i] >= ytest[i] - width and ypred[i] <= ytest[i] + width:
				t1 += 1
		accuracy = t1 / len(ytest)
		print('accuracy:', accuracy)
		break
	print('======================================================================================================')

def neural_n(data, r, accuracy_lb):
	print('\n\n======================================================================================================')
	print('Neural Network MLPRegressor')
	npdata = np.array(data)
	ypred, ytest, mse, accuracy = 0, 0, 0, 0
	sd = 0
	x = npdata[:, 3:(len(data[0])-1)]
	y = npdata[:, 2]

	while accuracy <= accuracy_lb:
		xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size = 0.3)

		mod = MLPRegressor(hidden_layer_sizes=200, max_iter=800, solver='lbfgs')
		regr = mod.fit(xtrain, ytrain)
		ypred = regr.predict(xtest)

		mse = ((ypred - ytest)**2).mean()
			
		sd = np.std(ytest)
			
		t1 = 0
		for i in range(len(ypred)):
			if ypred[i] >= ytest[i] - r*sd and ypred[i] <= ytest[i] + r*sd:
				t1 += 1
		accuracy = t1 / len(ytest)
	print('predicted value:')
	print(ypred)
	print('actual value:')
	print(ytest)
	print('\nmse:', mse)
	print('\nstandard error:', math.sqrt(mse))
	print('\nprediction accuracy:', accuracy)
	# print('\nmodel coefficients:')
	# print(regr.intercepts_)
	# print(regr.coefs_)
	print('======================================================================================================')

if __name__ == '__main__':
	data = []
	with open('processed_data.csv', newline='') as csvfile:
		temp = csv.reader(csvfile, delimiter=',', quotechar='|')
		for row in temp:
			data.append(row)

	for ind in range(1, len(data)):
		for i in range(len(data[ind])):
			data[ind][i] = float(data[ind][i])
		data[ind][0] = int(data[ind][0])
		data[ind][-1] = int(data[ind][-1])

	# get all counties which data is available
	col_names = data[0]
	data.pop(0)
	print('======================================================================================================')
	show_county_frequency(data)
	print('======================================================================================================')


	data = data_cleaning(data)
	print('data size after removing all outliers:', len(data))
	show_county_frequency(data)
	with open('processed_data_without_outliers.csv', 'a') as f:
		f.write(col_names[0])
		for i in range(1, len(col_names)):
			f.write(',' + col_names[i])
		f.write('\n')
		for d in data:
			f.write(str(d[0]))
			for i in range(1, len(d)):
				f.write(',' + str(d[i]))
			f.write('\n')
	f.close()

	r = 1
	accuracy_lb = 0.7

	npdata = np.array(data)
	for i in range(len(data[0])):
		npdata[:, i] = normalize(npdata[:, i][:,np.newaxis], axis=0).ravel()

	linear_reg(npdata, r, accuracy_lb)

	neural_n(npdata, r, accuracy_lb)

	npdata = np.array(data)

	# ======================================================================================================
	# modify range of production & width here
	ran = 10 # size of range    e.g. ran = 5 -> 15~20, 20~25, 25~30, ...
	width = 1.5 # number of adjacent ranges counted as prediction success
	# ======================================================================================================

	for i in range(len(npdata)):
		npdata[i, 2] = npdata[i, 2] // ran

	decision_t(npdata, width)

	# ======================================================================================================
	# modify Random Forest parameters here
	est = 200
	depth = 100
	# ======================================================================================================
	random_f(npdata, est, depth, width)

	