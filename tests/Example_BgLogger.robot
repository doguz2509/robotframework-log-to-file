*** Settings ***
Documentation    Suite description
Library   BuiltIn
Library  examples_bg_keywords.py

*** Test Cases ***
Test Bg log
    [Tags]    DEBUG
    Start thread  th1  my text1
    Start thread  th2  my text2
    BuiltIn.sleep  20s
    Stop thread  th1
    BuiltIn.sleep  20s
    Stop thread  th2
    [Teardown]  Stop logger

*** Keywords ***
Provided precondition
    Setup system under test