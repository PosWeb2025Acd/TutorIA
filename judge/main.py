import logging
import time

from judgement.llm import evaluation_from_llm
from evaluation.repository import create_evaluation_on_db
from user_and_answer.repository import get_question_and_answers_without_evaluation
from db.postgres import get_postgres_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Inicializando Juiz")

    while True:
        logger.info("Realizando julgamentos das ultimas questões")
        question_and_answer_list = get_question_and_answers_without_evaluation(get_postgres_connection())
        logger.info(f"Questões a serem avaliadas: {question_and_answer_list}")

        if question_and_answer_list is not None:
            for qa in question_and_answer_list:
                llm_evaluation = evaluation_from_llm(qa["question"], qa["answer"])
                logger.info(f"Resposta da llm: {llm_evaluation}")

                create_evaluation_on_db(get_postgres_connection(), qa["id"], llm_evaluation["reasoning"], llm_evaluation["score"])

        time.sleep(15)
