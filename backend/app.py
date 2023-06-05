from flask import Flask, request, jsonify
from collections import deque
from threading import Thread
import subprocess
import os
import logging
from flask_cors import CORS
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

REPO_DIR = 'neuraltimes'
REPO_URL = 'git@github.com:kazuuoooo/neuraltimes.git'
BRANCH_NAME = 'main'

queue = deque()
update_running = False


@app.route('/', methods=['GET'])
def home():
    return "Neural Times Backend!"


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return "", 204  # 204 status code means "No Content"


@app.route('/add', methods=['POST'])
def add_to_queue():
    global update_running
    data = request.get_json()
    topicinformation = data.get('topicinformation', None)
    sources = data.get('sources', None)

    if topicinformation is None or sources is None:
        return jsonify({'message': 'Bad Request'}), 400

    queue.append({
        'topicinformation': topicinformation,
        'sources': sources,
    })

    if not update_running:
        update_running = True
        Thread(target=start_job).start()

    return jsonify({'message': 'Added to queue'}), 200


@app.route('/queue', methods=['GET'])
def get_queue():
    return jsonify(list(queue)), 200


def start_job():
    global update_running
    try:
        job()
    except Exception as e:
        logging.error("An error occurred while processing the job: %s", str(e))
        update_running = False


def job():
    global update_running
    logging.info("Update Started")

    # Clone the repository
    run_command(['git', 'clone', '-b', BRANCH_NAME, REPO_URL], check=True, cwd=os.curdir)
    

    # Iterate over the queue until it is empty
    while len(queue) > 0:
        item = queue.popleft()

        # Here, you can do something with the item
        topicinformation = item['topicinformation']
        sources = item['sources']

        # Save the sources into sources.txt
        sources_file_path = os.path.join(REPO_DIR, "neuraltimes-generation-scripts", "topicinformation", 'sources.txt')
        with open(sources_file_path, 'w') as sources_file:
            sources_file.write(sources)

        # Save the topicinformation into gatheredinformation.txt
        gathered_information_file_path = os.path.join(REPO_DIR, "neuraltimes-generation-scripts", "topicinformation", 'gatheredinformation.txt')
        with open(gathered_information_file_path, 'w') as gathered_information_file:
            gathered_information_file.write(topicinformation)

        # Run the script
        run_command(['python', 'writer.py'], check=True, cwd=os.path.join(REPO_DIR, 'neuraltimes-generation-scripts'))

        # Move the generated content to the target directory
        generated_content_dir = os.path.join(REPO_DIR, 'neuraltimes-generation-scripts', 'generated-content')
        target_dir = os.path.join(REPO_DIR, '@elegantstack', 'site', 'content', 'posts')
        for filename in os.listdir(generated_content_dir):
            file_path = os.path.join(generated_content_dir, filename)
            shutil.move(file_path, target_dir)

    # Once the queue is empty, stage, commit, and push changes
   # run_command(['git', 'add', '@elegantstack/site/content/posts', '-A'], check=True, cwd=REPO_DIR)
   # run_command(['git', 'commit', '-m', 'Processed all items'], check=True, cwd=REPO_DIR)
   # run_command(['git', 'push', 'origin', BRANCH_NAME], check=True, cwd=REPO_DIR)

    # Delete the repository directory
    subprocess.run(['rm', '-rf', REPO_DIR], check=True)

    update_running = False
    logging.info("Update complete")

def run_command(command, **kwargs):
    try:
        subprocess.run(command, **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Command `{}` failed with error: {}".format(" ".join(e.cmd), str(e)))


if __name__ == '__main__':
    app.run(debug=True)