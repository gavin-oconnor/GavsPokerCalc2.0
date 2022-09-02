from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from random import randint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer)
    mode = db.Column(db.String) #multival, singleval, cash
    
    def __init__(self, mode):
        self.code = randint(0,10**4)
        temp_code = Game.query.filter_by(code=self.code).first()
        #generate codes until we find one not taken
        # we're good unless there are 10,000 concurrent games going
        while temp_code:
            self.code = randint(0,10**4)
            temp_code = Game.query.filter_by(code=self.code).first()
        self.mode = mode

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.Integer)
    buy_in = db.Column(db.Numeric)
    final_value = db.Column(db.Numeric)
    owe_string = db.Column(db.String)
    chip_string = db.Column(db.String)

    def __init__(self, name, code, buy_in, chip_string=""):
        self.name = name
        self.code = code
        self.buy_in = buy_in
        self.final_value = buy_in
        self.owe_string = ""
        self.chip_string = chip_string

class Player_Class:
    def __init__(self, name, buy_in, final_value):
        self.name = name
        self.buy_in = buy_in
        self.final_value = final_value
        self.owed = 0
        self.owes = 0
        self.owe_string = []

class Chip(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    code = db.Column(db.Integer)
    color = db.Column(db.String)
    value = db.Column(db.Numeric)

    def __init__(self, code, color, value):
        self.code = code
        self.color = color
        self.value = value

@app.route('/', methods=["GET","POST"])
def home():
    return render_template("home.html")

@app.route('/newgame', methods=["GET","POST"])
def newgame():
    return render_template("newgame.html")

@app.route('/equalchips', methods=["GET","POST"])
def equalchips():
    return render_template("equalchips.html")

@app.route('/creatediffvalues')
def creatediffvalues():
    new_game = Game("multival")
    db.session.add(new_game)
    db.session.commit()
    code = new_game.code
    return redirect(url_for("diffvalues",code=code))

@app.route('/diffvalues/<code>', methods=["GET","POST"])
def diffvalues(code):
    err = ""
    if request.method == "POST":
        chip_val = float(request.form['value'])
        chip_color = request.form['color'].lower().capitalize()
        if Chip.query.filter_by(code=code,color=chip_color).first():
            err = "That color is already in use"
        elif chip_val <= 0:
            err = "Chips must be worth more than $0.00"
        else:
            err = ""
            new_chip = Chip(code, chip_color, chip_val)
            db.session.add(new_chip)
            db.session.commit()
    chips = Chip.query.filter_by(code=code).all()
    return render_template("diffvalues.html",code=code,error=err,chips=chips)

@app.route('/usechips', methods=["GET","POST"])
def usechips():
    err = ""
    if request.method == "POST":
        chip_val = float(request.form['value'])
        if chip_val <= 0:
            err = "Chips must be worth more than $0.00"
        else:
            
            new_game = Game("singleval")
            db.session.add(new_game)
            db.session.commit()
            new_chip = Chip(new_game.code,"single",chip_val)
            db.session.add(new_chip)
            db.session.commit()
            return redirect(url_for("play",code=new_game.code))
    return render_template("usechips.html",error=err)

@app.route('/usecash',methods=["GET","POST"])
def usecash():
    new_game = Game("cash")
    db.session.add(new_game)
    db.session.commit()
    return redirect(url_for("play",code=new_game.code))

@app.route('/play/<code>', methods=["GET","POST"])
def play(code):
    print("THIS IS RUNNING")
    curr_game = Game.query.filter_by(code=code).first()
    print(curr_game.mode)
    if curr_game.mode == "cash":
        if request.method == "POST":
            name = request.form['name']
            if name is not None:
                is_a_player = Player.query.filter_by(code=code,name=name).first()
                money = request.form['value']
                if is_a_player is not None:
                    is_a_player.buy_in = money
                else:
                    new_player = Player(name, code, money)
                    db.session.add(new_player)
                db.session.commit()
        players = Player.query.filter_by(code=code).all()
        return render_template("cashplay.html",players=players,code=code)
    if curr_game.mode == "multival":
        chips = Chip.query.filter_by(code=code).all()
        if request.method == "POST":
            cs = ""
            name = request.form['name']
            is_a_player = Player.query.filter_by(code=code,name=name).first()
            money = 0
            if name is not None:
                for chip in chips:
                    money += int(request.form[f"{chip.color}"]) * chip.value
                    cs += str(request.form[f"{chip.color}"]) + "-"
                if is_a_player is not None:
                    is_a_player.buy_in = money
                    is_a_player.chip_string = cs
                else:
                    new_player = Player(name, code, money, cs)
                    db.session.add(new_player)
                db.session.commit()
        players = Player.query.filter_by(code=code).all()
        for player in players:
            temp = ""
            f = player.chip_string.split("-")
            for index, chip in enumerate(chips):
                if f[index] == "1":
                    temp += f"{f[index]} {chip.color} Chip - "
                else:
                    temp += f"{f[index]} {chip.color} Chips - "
            player.chip_string = temp[0:len(temp)-2]
        chips = Chip.query.filter_by(code=code).all()
        return render_template("multivalplay.html",chips=chips, players=players, code=code)
    else:
        print("RUN")
        chip_val = Chip.query.filter_by(code=code).first().value
        if request.method == "POST":
            name = request.form['name']
            if name is not None:
                chips = int(request.form['value'])
                money = chips * chip_val
                print(name)
                is_a_player = Player.query.filter_by(code=code,name=name).first()
                if is_a_player is not None:
                    print(is_a_player.name)
                    is_a_player.buy_in = money
                else:
                    new_player = Player(name, code, money)
                    db.session.add(new_player)
                db.session.commit()
        players = Player.query.filter_by(code=code).all()
        for player in players:
            player.buy_in /= chip_val
        return render_template("singlevalplay.html",players=players,code=code)

@app.route('/finishcashgame/<code>', methods=["GET","POST"])
def finish_cash_game(code):
    err = ""
    if request.method == "POST":
        err = ""
        buy_in_sum = 0
        final_sum = 0
        players = Player.query.filter_by(code=code).all()
        for player in players:
            
            final_val = request.form[f"{player.name}"]
            if final_val == '':
                err = "All fields must have a value"
                break
            final_val = float(final_val)
            player.final_value = final_val
            buy_in_sum += player.buy_in
            final_sum += player.final_value
        if buy_in_sum != final_sum:
            err = "Sum of final values must equal sum of buy ins"
        elif err == "":
            err = ""
            db.session.commit()
        # Add game ending here
            return redirect(url_for("finish",code=code))
    players = Player.query.filter_by(code=code).all()
    return render_template("finishcashgame.html",players=players,error=err)

@app.route('/finishchipgame/<code>', methods=["GET","POST"])
def finish_chip_game(code):
    err = ""
    chip_val = Chip.query.filter_by(code=code).first().value
    if request.method == "POST":
        err = ""
        buy_in_sum = 0
        final_val_sum = 0
        players = Player.query.filter_by(code=code).all()
        for player in players:
            final_val = request.form[f"{player.name}"]
            if final_val == '':
                err = "All fields must have a value"
                break
            final_val = int(request.form[f"{player.name}"])
            final_val_money = final_val * chip_val
            buy_in_sum += player.buy_in
            final_val_sum += final_val_money
            player.final_value = final_val_money
        if buy_in_sum != final_val_sum:
            err = "Sum of buy in chips must equal sum of final chips"
        elif err == "":
            db.session.commit()
            return redirect(url_for("finish",code=code))
        # Add game ending here
    players = Player.query.filter_by(code=code).all()
    for player in players:
        player.buy_in /= chip_val
    return render_template("finishchipgame.html",players=players,error=err)

@app.route('/finishmultigame/<code>', methods=["GET","POST"])
def finish_multi_game(code):
    err = ""
    chips = Chip.query.filter_by(code=code).all()
    players = Player.query.filter_by(code=code).all()
    for player in players:
        temp = ""
        f = player.chip_string.split("-")
        for index, chip in enumerate(chips):
            print(f[index])
            if f[index] == "1":
                temp += f"{f[index]} {chip.color} Chip -- "
            else:
                temp += f"{f[index]} {chip.color} Chips -- "
        player.chip_string = temp[0:len(temp)-3]
        player.buy_in = float(player.buy_in)
    players = Player.query.filter_by(code=code).all()
    if request.method == "POST":
        buy_in_sum = 0
        final_val_sum = 0
        for player in players:
            total = 0
            for chip in chips:
                amt = request.form[f"{player.name}-{chip.color}"]
                if amt == '':
                    err = "All fields must be filled"
                    break
                total +=  int(amt) * chip.value
            player.final_value = total
            buy_in_sum += player.buy_in
            final_val_sum += player.final_value
        if buy_in_sum != final_val_sum:
            err = "Sum of buy in chips must equal sum of final chips"
        else:
            db.session.commit()
            return redirect(url_for("finish",code=code))
            
    chips = Chip.query.filter_by(code=code).all()
    return render_template("finishmultigame.html",players=players,chips=chips,error=err)

@app.route('/finish/<code>')
def finish(code):
    players = Player.query.filter_by(code=code).all()
    player_objs = []
    for player in players:
        new_player_obj = Player_Class(player.name, player.buy_in, player.final_value)
        player_objs.append(new_player_obj)
    for player in player_objs:
        if player.buy_in > player.final_value:
            player.owes = player.buy_in - player.final_value
            player.owed = -1 * player.owes
        elif player.buy_in < player.final_value:
            player.owed = player.final_value - player.buy_in
    player_objs.sort(key=lambda x: x.owed)
    big_loser = player_objs[0].name
    down_amount = int(player_objs[0].owes)

    for player in player_objs:
        index = len(player_objs) - 1
        while player.owed > 0:
            if player_objs[index].owes == 0:
                pass
            elif player_objs[index].owes >= player.owed:
                sstr = "{:.2f}".format(player.owed)
                player_objs[index].owe_string.append(f"{player_objs[index].name} owes {player.name} ${sstr}")
                temp_owes = player_objs[index].owes
                player_objs[index].owes -= player.owed
                player.owed -= temp_owes
            elif player_objs[index].owes < player.owed:
                paying = player_objs[index].owes
                sstr = "{:.2f}".format(paying)
                player_objs[index].owe_string.append(f"{player_objs[index].name} owes {player.name} ${sstr}")
                player.owed -= paying
                player_objs[index].owes -= paying
            index -= 1
    owe_strings = []
    for player in player_objs:
        owe_strings.append(player.owe_string)
    
    return render_template("finish.html",owe_strings=owe_strings,big_loser=big_loser,down_amount=down_amount)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=False)
