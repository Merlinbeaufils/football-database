"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.94.195/proj1part2
#
#     my version:
#     postgresql://mb4988:mbjb@34.75.94.195/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.94.195/proj1part2"
#
DATABASEURI = "postgresql://mb4988:mbjb@34.75.94.195/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS filter (
  nationality varchar(30),
  goals int,
  ranking int,
  country varchar(30),
  player_filter int,
  team_filter int,
  league_filter int,
  extended int
);""")
engine.execute('DELETE FROM filter;')
engine.execute('INSERT INTO filter(goals, ranking) VALUES (0, 20);')

engine.execute("""CREATE TABLE IF NOT EXISTS filter_leagues (
  league_name varchar(30)
);""")

engine.execute("""CREATE TABLE IF NOT EXISTS filter_players (
  playername varchar(30)
);""")

engine.execute("""CREATE TABLE IF NOT EXISTS filter_teams (
  team_name varchar(30)
);""")


@app.before_request
def before_request():
    """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def root():
    """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)

    # cursor = g.conn.execute("SELECT name FROM test")
    # names = []
    # for result in cursor:
    #   names.append(result['name'])  # can also be accessed using result[0]
    # cursor.close()
    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    # context = dict(data = names)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("root.html", **{})


#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/compare_players')
def compare_players():
    team_filter = next(g.conn.execute("SELECT MAX(f.team_filter) AS max FROM filter f;"))['max']
    league_filter = next(g.conn.execute("SELECT MAX(f.league_filter) AS max FROM filter f;"))['max']
    extended = next(g.conn.execute("SELECT MAX(f.extended) AS max FROM filter f;"))['max']
    g.conn.execute("DELETE FROM filter_players;")

    filter_nationalities = g.conn.execute(
        "SELECT DISTINCT f.nationality FROM filter f WHERE f.nationality IS NOT NULL;")

    if team_filter:
        players = g.conn.execute("""SELECT DISTINCT p.playername, p.nationality, p.age, p.position, p.goals FROM players p, Is_Part_Of i, filter_teams f 
                            WHERE i.team_name = f.team_name AND p.playername = i.playername;""")
    elif league_filter:
        players = g.conn.execute("""SELECT DISTINCT p.playername, p.nationality, p.age, p.position, p.goals FROM players p, Is_Part_Of i, registered_in r, filter_leagues f
                            WHERE i.team_name = r.team_name AND r.league_name = f.league_name AND p.playername = i.playername;""")

    elif not [player for player in filter_nationalities]:
        players = g.conn.execute(
            "SELECT DISTINCT p.playername, p.nationality, p.age, p.position, p.goals FROM players P WHERE P.goals >= (SELECT MAX(f.goals) FROM filter f)")
    else:
        players = g.conn.execute(
            "SELECT DISTINCT p.playername, p.nationality, p.age, p.position, p.goals FROM players P, filter f WHERE P.nationality = f.nationality AND P.goals >= (SELECT MAX(f.goals) FROM filter f);")

    p = [player for player in players]
    players.close()
    player_names = list(set(player['playername'] for player in p))
    nationalities_list = list(set(nationality['nationality'] for nationality in p))


    [g.conn.execute("INSERT INTO filter_players(playername) values (%s);", name) for name in player_names]
    g.conn.execute("DELETE FROM filter_teams;")
    g.conn.execute("DELETE FROM filter_leagues;")

    if extended:
        new = [dict(playername=pl['playername'], nationality=pl['nationality'],
                           age=pl['age'], position=pl['position'], goals=pl['goals']) for pl in p]
    else:
        new = [dict(playername=pl['playername'], nationality=pl['nationality']) for pl in p]

    context = dict(data=new, extended=bool(extended))
    return render_template("compare_players.html", **context)


@app.route('/compare_teams')
def compare_teams():
    league_filter = next(g.conn.execute("SELECT MAX(f.league_filter) AS max FROM filter f;"))['max']
    player_filter = next(g.conn.execute("SELECT MAX(f.player_filter) AS max FROM filter f;"))['max']
    g.conn.execute("DELETE FROM filter_teams;")
    extended = next(g.conn.execute("SELECT MAX(f.extended) AS max FROM filter f;"))['max']


    filter_league_names = g.conn.execute("SELECT DISTINCT f.country FROM filter f WHERE f.country IS NOT NULL;")

    if league_filter:
        teams = g.conn.execute("""SELECT DISTINCT t.team_name, t.governing_country, t.manager, t.league_standing, t.goals_for FROM teams t, registered_in i, filter_leagues f 
                            WHERE i.league_name = f.league_name AND t.team_name = i.team_name;""")
    elif player_filter:
        teams = g.conn.execute("""SELECT DISTINCT t.team_name, t.governing_country, t.manager, t.league_standing, t.goals_for FROM Is_Part_Of i, filter_players f, teams t
                            WHERE i.playername = f.playername AND t.team_name = i.team_name;""")

    elif not [team for team in filter_league_names]:
        teams = g.conn.execute(
            "SELECT DISTINCT t.team_name, t.governing_country, t.manager, t.league_standing, t.goals_for FROM teams t WHERE t.league_standing <= (SELECT MAX(f.ranking) FROM filter f)")
    else:
        teams = g.conn.execute(
            "SELECT DISTINCT t.team_name, t.governing_country, t.manager, t.league_standing, t.goals_for FROM teams t, filter f WHERE t.league_name = f.country AND t.league_standing <= (SELECT MIN(g.ranking) FROM filter g;")

    t = [team for team in teams]
    nationalities_list = list(set(team['governing_country'] for team in t))
    team_names = list(set(team['team_name'] for team in t))
    teams.close()

    [g.conn.execute("INSERT INTO filter_teams(team_name) values (%s);", name) for name in team_names]
    g.conn.execute("DELETE FROM filter_players;")
    g.conn.execute("DELETE FROM filter_leagues;")

    if extended:
        new = [dict(team_name=pl['team_name'], country=pl['governing_country'],
                    manager=pl['manager'], league_standing=pl['league_standing'], goals=pl['goals_for']) for pl in t]
    else:
        new = [dict(team_name=pl['team_name'], country=pl['governing_country']) for pl in t]

    context = dict(data=new, extended=bool(extended))
    return render_template("compare_teams.html", **context)


@app.route('/compare_leagues')
def compare_leagues():
    team_filter = next(g.conn.execute("SELECT MAX(f.team_filter) AS max FROM filter f;"))['max']
    player_filter = next(g.conn.execute("SELECT MAX(f.player_filter) AS max FROM filter f;"))['max']
    g.conn.execute("DELETE FROM filter_leagues;")
    extended = next(g.conn.execute("SELECT MAX(f.extended) AS max FROM filter f;"))['max']


    if player_filter:
        leagues = g.conn.execute("""SELECT DISTINCT l.league_name, l.lastplaceteam, l.firstplaceteam FROM leagues l, Is_Part_Of i, registered_in r, filter_players f
                            WHERE r.team_name = i.team_name AND i.playername = f.playername AND l.league_name = r.league_name;""")
    elif team_filter:
        leagues = g.conn.execute("""SELECT DISTINCT l.league_name, l.lastplaceteam, l.firstplaceteam FROM registered_in r, filter_teams f, leagues l
                            WHERE r.team_name = f.team_name AND l.league_name = r.league_name;""")
    else:
        leagues = g.conn.execute("SELECT DISTINCT l.league_name, l.lastplaceteam, l.firstplaceteam FROM leagues l")

    l = [league for league in leagues]
    league_names = [league['league_name'] for league in l]
    leagues.close()

    [g.conn.execute("INSERT INTO filter_leagues(league_name) values (%s);", name) for name in league_names]
    g.conn.execute("DELETE FROM filter_players;")
    g.conn.execute("DELETE FROM filter_teams;")

    if extended:
        new = [dict(league_name=pl['league_name'], firstplaceteam=pl['firstplaceteam'], lastplaceteam=pl['lastplaceteam']) for pl in l]
    else:
        new = [dict(league_name=pl['league_name']) for pl in l]

    context = dict(data=new, extended=bool(extended))
    return render_template("compare_leagues.html", **context)


# Example of adding new data to the database
@app.route('/add_to_nationality', methods=['POST'])
def add_to_nationality():
    name = request.form['name']
    g.conn.execute('INSERT INTO filter(nationality) VALUES (%s)', name)
    return redirect('/compare_players')


@app.route('/add_to_goals', methods=['POST'])
def add_to_goals():
    name = request.form['name']
    g.conn.execute('INSERT INTO filter(goals) VALUES (%s)', name)
    return redirect('/compare_players')


@app.route('/add_to_country', methods=['POST'])
def add_to_country():
    name = request.form['name']
    g.conn.execute('INSERT INTO filter(country) VALUES (%s)', name)
    return redirect('/compare_teams')


@app.route('/add_to_ranking', methods=['POST'])
def add_to_ranking():
    name = request.form['name']
    g.conn.execute('INSERT INTO filter(ranking) VALUES (%s)', name)
    return redirect('/compare_teams')


@app.route('/reset_filter_players')
def reset_filter_players():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking) VALUES (0, 20);')
    return redirect('/compare_players')


@app.route('/reset_filter_teams')
def reset_filter_teams():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking) VALUES (0, 20);')
    return redirect('/compare_teams')


@app.route('/reset_filter_leagues')
def reset_filter_leagues():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking) VALUES (0, 20);')
    return redirect('/compare_leagues')


@app.route('/go_to_players_from_leagues')
def go_to_players_from_leagues():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, league_filter, team_filter) VALUES (0, 20, 0, 1);')
    return redirect('/compare_players')


@app.route('/go_to_players_from_teams')
def go_to_players_from_teams():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, team_filter) VALUES (0, 20, 1);')
    return redirect('/compare_players')


@app.route('/go_to_leagues_from_players')
def go_to_leagues_from_players():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, player_filter) VALUES (0, 20, 1);')
    return redirect('/compare_leagues')


@app.route('/go_to_leagues_from_teams')
def go_to_leagues_from_teams():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, team_filter) VALUES (0, 20, 1);')
    return redirect('/compare_leagues')


@app.route('/go_to_teams_from_players')
def go_to_players_from_league():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, player_filter) VALUES (0, 20, 1);')
    return redirect('/compare_teams')


@app.route('/go_to_teams_from_leagues')
def go_to_teams_from_leagues():
    g.conn.execute('DELETE FROM filter;')
    g.conn.execute('INSERT INTO filter(goals, ranking, league_filter) VALUES (0, 20, 1);')
    return redirect('/compare_teams')

@app.route('/detailed_view_players')
def detailed_view_players():
    g.conn.execute('INSERT INTO filter(extended) VALUES (1);')
    return redirect('/compare_players')

@app.route('/detailed_view_teams')
def detailed_view_teams():
    g.conn.execute('INSERT INTO filter(extended) VALUES (1);')
    return redirect('/compare_teams')

@app.route('/detailed_view_leagues')
def detailed_view_leagues():
    g.conn.execute('INSERT INTO filter(extended) VALUES (1);')
    return redirect('/compare_leagues')



# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
#   return redirect('/')


@app.route('/login')
def login():
    os.abort(401)
    raise AssertionError
    # this_is_never_executed()


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=5432, type=int)
    def run(debug, threaded, host, port):
        """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
