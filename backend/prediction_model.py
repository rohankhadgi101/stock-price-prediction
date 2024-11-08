import pandas as pd
import numpy as np
import datetime as dt
import sys
import yfinance as yf
from NeuralNetworks.lstm import LSTM
from utils import *
from normalize import Normalize


def lstm_predict(stock, start, end):
    # get stock data
    try:
        df, data = get_stock_data(stock, start, end, json=False)
    except:
        # error info
        e = sys.exc_info()
        print(e)
        print("lstm predict fail")
        return {"error": e}

    stock = df
    data = data.reset_index()
    trend_dates = pd.to_datetime(data["Date"]).map(lambda x: str(x.date())).tolist()
    
    scaler = Normalize(df)
    df = scaler.normalize_data(df)

    train_max_index = round((len(df) - 1) * 0.80)

    training_input_1 = [[df[i-6], df[i-5]] for i in range(6, train_max_index)]
    training_input_2 = [[df[i-4], df[i-3]] for i in range(6, train_max_index)]
    training_input_3 = [[df[i-2], df[i-1]] for i in range(6, train_max_index)]
    target = [[i] for i in df[6:train_max_index]]

    training_input_1 = np.array(training_input_1, dtype=float)
    training_input_2 = np.array(training_input_2, dtype=float)
    training_input_3 = np.array(training_input_3, dtype=float)
    target = np.array(target, dtype=float)

    assert len(training_input_1) == len(training_input_2) == len(training_input_3) == len(target)

    # create neural network
    NN = LSTM()

    # number of training cycles
    training_cycles = 10

    # train the neural network
    for cycle in range(training_cycles):
        for n in range(0, len(target)):
            output = NN.train(training_input_1, training_input_2, training_input_3, target)


    # de-Normalize
    output = scaler.denormalize_data(output)
    target = scaler.denormalize_data(target)

    # transpose
    output = output.T

    # change data type so it can be plotted
    prices = pd.DataFrame(output)

    # [price 2 days ago, price yesterday] for each day in range
    testing_input_1 = [[df[i-6], df[i-5]] for i in range(train_max_index, len(df))]
    testing_input_2 = [[df[i-4], df[i-3]] for i in range(train_max_index, len(df))]
    testing_input_3 = [[df[i-2], df[i-1]] for i in range(train_max_index, len(df))]
    test_target = [[i] for i in df[train_max_index:len(df)]]

    assert len(testing_input_1) == len(testing_input_2) == len(testing_input_3) == len(test_target)

    testing_input_1 = np.array(testing_input_1, dtype=float)
    testing_input_2 = np.array(testing_input_2, dtype=float)
    testing_input_3 = np.array(testing_input_3, dtype=float)
    test_target = np.array(test_target, dtype=float)

    # test the network with unseen data
    test = NN.test(testing_input_1, testing_input_2, testing_input_3)

    # de-Normalize data
    test = scaler.denormalize_data(test)
    test_target = scaler.denormalize_data(test_target)

    # transplose test results
    test = test.T

    # accuracy
    train_accuracy = 100 - mape(target, output)
    print("------------ TRAINING STATS ------------")
    print("Accuracy in %: ", train_accuracy)
    print("Mean Squared Error (MSE) : ", mse(target, output))
    print("Root Mean Square Error (RMSE) : ", rmse(target, output))

    # accuracy
    test_accuracy = 100 - mape(test_target, test)
    print("\n------------ TESTING STATS ------------")
    print("Accuracy in %: ", test_accuracy)
    print("Mean Squared Error (MSE) : ", mse(test_target, test))
    print("Root Mean Square Error (RMSE) : ", rmse(test_target, test))
    
    num_days = 0
    predict = []
    if(dt.datetime(*end) > dt.datetime.today()):
        num_days = (dt.datetime(*end) - dt.datetime.today()).days
        print("DAYS : ", num_days)

        pred_input = pd.DataFrame(test)
        pred_input = pred_input[0].tail(n=100)
        scaler = Normalize(pred_input)
        pred_input = scaler.normalize_data(pred_input)

        # prediction for future
        prediction_input_1 = [[pred_input[i-6], pred_input[i-5]] for i in range(6, len(pred_input))]
        prediction_input_2 = [[pred_input[i-4], pred_input[i-3]] for i in range(6, len(pred_input))]
        prediction_input_3 = [[pred_input[i-2], pred_input[i-1]] for i in range(6, len(pred_input))]
        predict_target = [[i] for i in pred_input[6:len(pred_input)]]

        assert len(prediction_input_1) == len(prediction_input_2) == len(prediction_input_3) == len(predict_target)

        prediction_input_1 = np.array(prediction_input_1, dtype=float)
        prediction_input_2 = np.array(prediction_input_2, dtype=float)
        prediction_input_3 = np.array(prediction_input_3, dtype=float)
        predict_target = np.array(predict_target, dtype=float)

        # test the network with unseen data
        predict = NN.test(prediction_input_1, prediction_input_2, prediction_input_3)

        # de-Normalize data
        predict = scaler.denormalize_data(predict)
        predict_target = scaler.denormalize_data(predict_target)

        # transplose test results
        predict = predict.T

    return (
        stock, 
        trend_dates, 
        prices, 
        pd.DataFrame(test), 
        pd.DataFrame(predict), 
        str(round(test_accuracy, 2)), 
        str(round(train_accuracy, 2)), 
        str(round(mse(target, output), 5)),
        str(round(mse(test_target, test), 5)),
        str(round(rmse(target, output), 5)),
        str(round(rmse(test_target, test), 5)),
        num_days
    )

def get_stock_data(ticker, start=[2020, 1, 1], end=[2024, 1, 1], json=True):
    # *list passes the values in list as parameters
    start = dt.datetime(*start)
    end = dt.datetime(*end)

    # download csv from yahoo finance
    try:
        data = yf.download(ticker, start, end)
    except:
        # error info
        e = sys.exc_info()
        print(e)
        print("get data fail")
        return e

    # extract adjusted close column
    df = data["Adj Close"]
    # remove Date column
    df = pd.DataFrame([i for i in df])[0]
    if json:
        # return data as JSON
        return df.to_json()

    else:
        # return data as csv
        return df, data

