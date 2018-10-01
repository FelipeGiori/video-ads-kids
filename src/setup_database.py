#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from database_model import create_db

def check_database():
    create_db()
    
def main():
    create_db()
    
if __name__ == "__main__":
    main()