import os
from lambda_functions.create_alter_athena_view import util
from pathlib import Path

def test_util():

    test_statement = util.load_query(Path(__file__).parent.joinpath('test.sql'),
                                                         {"mykey": "myplaceholdervalue",
                                                          "myotherkey": "myotherplaceholder"})
    
    assert test_statement == "CREATE OR REPLACE VIEW \"myplaceholdervalue\" AS ...\nCREATE OR REPLACE VIEW \"myotherplaceholder\" AS ..."
