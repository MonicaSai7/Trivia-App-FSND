import re
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request, data):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  selection = [record.format() for record in data]
  current_selection = selection[start:end]

  return current_selection

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={'/': {'origins': '*'}})

  '''
  after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    """ Set Access Control """

    response.headers.add(
      'Access-Control-Allow-Headers',
      'Content-Type, Authorization, true')
    response.headers.add(
      'Access-Control-Allow-Methods',
      'GET, POST, PATCH, DELETE, OPTIONS')

    return response

  '''
  Endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_all_categories():

    try:
      categories = Category.query.all()
      categories_dict = {}
      for category in categories:
        categories_dict[category.id] = category.type
      
      if len(categories_dict) == 0:
        abort(404)
      
      return jsonify({
        'success': True,
        'categories': categories_dict
      })

    except Exception:
      abort(500)

  '''
  Endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  '''
  @app.route("/questions")
  def get_questions():
    all_questions = Question.query.all()
    questions_count = len(all_questions)
    current_questions = paginate(request, all_questions)

    all_categories = Category.query.all()
    categories_dict = {}
    for category in all_categories:
      categories_dict[category.id] = category.type
    
    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': questions_count,
      'categories': categories_dict
    })

  '''
  Endpoint to DELETE question using a question ID. 
  '''
  @app.route("/questions/<int:id>", methods=["DELETE"])
  def delete_question(id):
    try:
      question = Question.query.filter_by(id=id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      return jsonify({
        'success': True,
        'deleted': id
      })
    except:
      abort(422)

  '''
  Endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.
  '''
  @app.route('/questions', methods=["POST"])
  def add_question():
    json_body = request.get_json()

    question = json_body.get('question', '')
    answer = json_body.get('answer', '')
    difficulty = json_body.get('difficulty', '')
    category = json_body.get('category', '')

    if question == '' or answer == '' or difficulty == '' or category == '':
      abort(422)
    
    try:
      question_instance = Question(
        question=question,
        answer=answer,
        difficulty=difficulty,
        category=category
      )

      question_instance.insert()

      return jsonify({
        'success': True,
        'message': 'Question creation successful!'
      }), 201
    
    except Exception:
      abort(422)

  '''
  POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():

    json_body = request.get_json()
    search_term = json_body.get('searchTerm')

    if search_term == '':
      abort(422)
    
    try:
      
      questions = [question.format() for question in Question.query.all() if
                      re.search(search_term, question.question, re.IGNORECASE)]
      
      if len(questions) == 0:
        abort(404)
      
      questions_count = len(questions)

      return jsonify({
        'success': True,
        'questions': questions,
        'total_questions': questions_count
      }), 200
    
    except Exception:
      abort(404)

  '''
  GET endpoint to get questions based on category. 
  '''
  @app.route("/categories/<int:id>/questions", methods=['GET'])
  def get_questions_by_category(id):

    category = Category.query.filter_by(id=id).one_or_none()

    if category is None:
      abort(422)

    questions = Question.quert.filter_by(category=id).all()
    paginated_questions = paginate(request, questions)
    
    return jsonify({
      'success': True,
      'questions': paginated_questions,
      'total_questions': len(questions),
      'current_category': category.type
    })  

  '''
  POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 
  '''
  @app.route("/quizzes", methods=['POST'])
  def play_quiz():

    json_body = request.get_json()
    previous_questions = json_body.get('previous_questions')
    quiz_category = json_body.get('quiz_category')

    if previous_questions is None or quiz_category is None:
      abort(400)

    if quiz_category['id'] == 0:
      questions = Question.query.all()
    else:
      questions = Question.query.filter_by(category=quiz_category['id']).all()
    
    def get_random_question():
      return questions[random.randint(0, len(questions) - 1)]

    next_question = get_random_question()
    not_found = True
    while not_found:
      if next_question.id in previous_questions:
        next_question = get_random_question()
      else:
        not_found = False
    
    return jsonify({
      'success': True,
      'question': next_question.format()
    }), 200

  '''
  Error handlers for all expected errors
  '''
  # Error handler for Bad request error (400)
  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          'success': False,
          'error': 400,
          'message': 'Bad request error'
      }), 400

  # Error handler for resource not found (404)
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          'success': False,
          'error': 404,
          'message': 'Resource not found'
      }), 404

  # Error handler for internal server error (500)
  @app.errorhandler(500)
  def internal_server_error(error):
      return jsonify({
          'success': False,
          'error': 500,
          'message': 'An error has occured, please try again'
      }), 500

  # Error handler for unprocesable entity (422)
  @app.errorhandler(422)
  def unprocesable_entity(error):
      return jsonify({
          'success': False,
          'error': 422,
          'message': 'Unprocessable entity'
      }), 422
  
  return app

  