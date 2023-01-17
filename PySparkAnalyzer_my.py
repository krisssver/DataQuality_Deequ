import argparse
import os
os.environ['SPARK_VERSION'] = '3.1'

import pydeequ
from pydeequ.profiles import *
from pydeequ.analyzers import *
from pydeequ.checks import *
from pydeequ.verification import *
from pyspark.sql import SparkSession


def process(spark, data_path, report_path):
    """
    Основной процесс задачи.

    :param spark: SparkSession
    :param data_path: путь до датасета
    :param report_path: путь сохранения отчета
    """
    df = spark.read.parquet(data_path)
    
    analyzer = AnalysisRunner(spark) \
                    .onData(df) \
                    .addAnalyzer(Size()) \
                    .addAnalyzer(Completeness("id")) \
                    .addAnalyzer(Completeness("vendor_code")) \
                    .addAnalyzer(Completeness("name")) \
                    .addAnalyzer(Completeness("type")) \
                    .addAnalyzer(Completeness("label")) \
                    .addAnalyzer(Completeness("price")) \
                    .addAnalyzer(Completeness("discount")) \
                    .addAnalyzer(Completeness("available_count")) \
                    .addAnalyzer(Completeness("preorder_count")) \
                    .addAnalyzer(Compliance("discount less than 0", 'discount<0')) \
                    .addAnalyzer(Compliance("discount great than 100", 'discount>100')) \
                    .addAnalyzer(Compliance("available_count less than 0", 'available_count<0')) \
                    .addAnalyzer(Compliance("preorder_count less than 0", 'preorder_count<0')) \
                    .run()
    
    analysisResult_df1 = AnalyzerContext.successMetricsAsDataFrame(spark, analyzer)
    
    
    
    check_unique = Check(spark, CheckLevel.Error, "Unique ID")\
        .isUnique("id")

    checkResult = VerificationSuite(spark) \
        .onData(df) \
        .addCheck(check_unique) \
        .run()
    
    analysisResult_df2 = VerificationResult.successMetricsAsDataFrame(spark, checkResult)
    
    
    analysisResult_df = analysisResult_df1.union(analysisResult_df2)
    
    
    analysisResult_df.write.parquet(report_path)


def main(data_path, report_path):
    spark = _spark_session()
    process(spark, data_path, report_path)


def _spark_session():
    """
    Создание SparkSession.

    :return: SparkSession
    """
    return SparkSession \
        .builder.appName('PySparkAnalyzer') \
        .config("spark.jars.packages", pydeequ.deequ_maven_coord) \
        .config("spark.jars.excludes", pydeequ.f2j_maven_coord) \
        .getOrCreate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data.parquet', help='Please set datasets path.')
    parser.add_argument('--report_path', type=str, default='report', help='Please set target report path.')
    args = parser.parse_args()
    data_path = args.data_path
    report_path = args.report_path
    main(data_path, report_path)
