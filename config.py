import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///mrp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Company details — used in all printed documents
    COMPANY_NAME = 'DT Solutions Ltd'
    COMPANY_REG = '06593337'
    COMPANY_VAT = '996313288'
    COMPANY_TEL = '01452 332727'
    COMPANY_FAX = '01452 332828'
    COMPANY_EMAIL = 'contact@dtsolutionsltd.co.uk'
    # Accounts / registered address (PO, Invoice)
    COMPANY_ADDR1 = 'Unit 7 Woodrow Way'
    COMPANY_ADDR2 = 'Gloucester'
    COMPANY_POSTCODE = 'GL2 5DX'
    # Dispatch / warehouse address (Delivery Notes)
    COMPANY_DISPATCH_ADDR1 = 'Unit 4, Tuffley Industrial Park, Pearce Way'
    COMPANY_DISPATCH_ADDR2 = 'Gloucester'
    COMPANY_DISPATCH_POSTCODE = 'GL2 5YD'
    # Bank details
    COMPANY_BANK = 'HSBC Bank'
    COMPANY_SORT_CODE = '40-22-09'
    COMPANY_ACCOUNT = '72385880'

config = {
    'development': Config,
    'production': Config,
    'testing': Config
}
