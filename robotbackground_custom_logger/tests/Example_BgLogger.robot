*** Settings ***
Documentation    Suite description
Library   BuiltIn
Library  examples_bg_keywords.py

*** Test Cases ***
Test Bg log start
    [Tags]    DEBUG

    Start thread  th1
    Start thread  th2
    Start thread  th3
    Start thread  th4
    Start thread  th5
    Start thread  th6
    Start thread  th7
    Start thread  th8
    Start thread  th9
    Start thread  th10
    Start thread  th11
    Start thread  th12
    Start thread  th13
    BuiltIn.sleep  20s

Test Bg log stop
    Stop thread  th1
    BuiltIn.sleep  5s
    Stop thread  th2
    BuiltIn.sleep  5s
    Stop thread  th3
    BuiltIn.sleep  5s
    Stop thread  th4
    BuiltIn.sleep  5s
    Stop thread  th5

    BuiltIn.sleep  5s
    Stop thread  th6
    BuiltIn.sleep  5s
    Stop thread  th7

    BuiltIn.sleep  20s
    Stop all
    [Teardown]  Stop logger

*** Keywords ***
Provided precondition
    Setup system under test