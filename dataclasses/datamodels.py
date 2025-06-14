from .enum_ext import EnumExt # pylint: disable= E0402

class JournalCodeEnum(EnumExt):
    AYA_PAY = ("aya_pay", "AYA Pay")
    CB_PAY = ("cb_pay", "CB Pay")
    CITIZENS_PAY = ("citizens_pay", "Citizens Pay")
    JCB = ("jcb", "JCB")
    KBZ_MOBILE_BANKING = ("kbz_mobile_banking", "KBZ Mobile Banking")
    KBZ_PAY = ("k_pay", "KBZ Pay")
    MAB_MOBILE_BANKING = ("mab_mobile_banking", "MAB Mobile Banking")
    MASTER = ("master", "Master")
    M_PITE_SAN = ("m_pite_san", "M-Pite san")
    MPT_PAY = ("mpt_pay", "MPT Pay")
    MPU = ("mpu", "MPU")
    MYTEL_PAY = ("mytel_pay", "Mytel Pay")
    OK_DOLLAR = ("ok_dollar", "OK Dollar")
    ONE_PAY = ("onepay", "One Pay")
    SAI_SAI_PAY = ("sai_sai_pay", "Sai Sai Pay")
    TRUE_MONEY = ("true_money", "True Money")
    UAB_PAY = ("uab_pay", "UAB Pay")
    VISA = ("visa", "Visa")
    WAVE_PAY = ("wave_pay", "Wave Pay")

class TransactionStatusEnum(EnumExt):
    DRAFT = ("draft", "DRAFT")
    SUCCESS = ("success", "SUCCESS")
    DECLINED = ("decline", "DECLINED")
    TIMEOUT = ("timeout", "TIMEOUT")
    CANCELLED =("cancel", "CANCELLED")
    SYSTEM_ERROR = ("system_error", "SYSTEM_ERROR")
    ERROR = ("error", "ERROR")

class TransactionEnum(EnumExt):
    DINGER = "dinger"
    ORDER = "merchant_order"
    PROVIDER = "provider_name"
    REFERENCE = "reference"
    TRANSATION_ID = "transaction_id"
