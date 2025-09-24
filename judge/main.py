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
        db_connection = get_postgres_connection()

        question_and_answer_list = get_question_and_answers_without_evaluation(db_connection, limit=10)

        if question_and_answer_list is not None:
            for qa in question_and_answer_list:
                llm_evaluation = evaluation_from_llm(qa["question"], qa["answer"])
                logger.info(f"Julgamento da quest '{qa["question"]}' realizado com sucesso. Nota: {llm_evaluation["score"]}")
                create_evaluation_on_db(db_connection, qa["id"], llm_evaluation["reasoning"], llm_evaluation["score"])

            logger.info("Julgamentos finalizados, aguardando 15 segundos para nova rodada")
        else:
            logger.info("Nenhum novo par questão e resposta para julgar, aguardando 15 segundos para nova rodada")

        db_connection.close()
        time.sleep(15)
