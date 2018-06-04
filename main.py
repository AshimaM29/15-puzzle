from flask import Flask, render_template, request, redirect, url_for, json
from flaskext.mysql import MySQL
from decimal import Decimal
from IDAStar import *

app = Flask(__name__)
app.secret_key = 'ssh...Big secret!'

mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'puzzle'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/userpuzzle")
def userpuzzle():
    return render_template('userpuzzle.html')	

@app.route("/systempuzzle")
def systempuzzle():
	return render_template('systempuzzle.html')

@app.route('/handle_system_data', methods=['POST'])
def handle_system_data():
	try:
		config = request.form['config'].split(',')
		numbers = [ int(x) for x in config ]

		solved_state = slide_solved_state(4)
		neighbours = slide_neighbours(4)
		is_goal = lambda p: p == solved_state

		slide_solver = IDAStar(slide_wd(4, solved_state), neighbours)
		
		p = tuple(numbers)
		startTime = int(round(time.time() * 1000))
		print type(startTime)
		path, moves, cost, num_eval = slide_solver.solve(p, is_goal, 80)
		slide_print(p)
		endTime = int(round(time.time() * 1000))
		print endTime
		print(", ".join({-1: "Left", 1: "Right", -4: "Up", 4: "Down"}[move[1]] for move in moves))
		print(cost, num_eval)
		timeTaken = (Decimal(endTime) - Decimal(startTime))/1000
		print timeTaken

		conn = mysql.connect()
		cursor = conn.cursor()

		role = "System"
		cursor.execute("INSERT INTO result(config,time,role) VALUES(%s,%s,%s)", (request.form['config'],timeTaken,role))
		conn.commit()

		data_dict = {
			'moves':cost,
			'time': timeTaken
		}

		return render_template('systemResult.html', data_dict = data_dict)

	except Exception as e:
		return json.dumps({'error':str(e)})
	finally:
		cursor.close()
		conn.close()

@app.route("/topResults")
def topResults():
	conn = mysql.connect()
	cursor = conn.cursor()

	cursor.execute("SELECT * FROM result ORDER BY time LIMIT 10")
	data = cursor.fetchall()

	data_dict = []
	for i in data:
		data_dic = {
			'config': i[1],
			'time': i[2],
			'role': i[3]
		}
		data_dict.append(data_dic)

	loopdata = data_dict

	return render_template('topResults.html', loopdata = loopdata)

@app.route('/handle_user_data', methods=['POST'])
def handle_user_data():
	role = "User"
	try:
		timeTaken = Decimal(request.form['timeTaken'])
		config = request.form['config']

		conn = mysql.connect()
		cursor = conn.cursor()

		cursor.execute("INSERT INTO result(config,time,role) VALUES(%s,%s,%s)", (config,timeTaken,role))
		conn.commit()
		return redirect(url_for('main'))
	except Exception as e:
		return json.dumps({'error':str(e)})

if (__name__ == "__main__"):
	app.debug = True
	app.run()
