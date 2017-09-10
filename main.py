import parser

parser = parser.PageParser(debug=True)
df = parser.get_data()
df.to_pickle('cars_df.pikle')
