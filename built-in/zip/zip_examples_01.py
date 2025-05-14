

datas = [[1, 'a', 2, 'b', 3], ['c', 4, 'd', 5, 'e']]
types = [['int', 'str', 'int', 'str', 'int'], ['str', 'int', 'str', 'int', 'str']]
zip_datas = [list(zip(datas[i], types[i][:])) for i in range(len(datas))]
print(zip_datas)
