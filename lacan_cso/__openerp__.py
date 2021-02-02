##############################################################################
#
# LACAN Technologies Sp. z o.o.
# Al. Stanow Zjednoczonych 53
# 04-028 Warszawa
#
# Copyright (C) 2009-2014 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
#
##############################################################################

{
    "name" : "CSO Data Import",
    "version" : "1.0",
    "author" : "developers@lacan.com.pl",
    "description" : """
        Data Import
    """,
    "website" : "http://www.lacan.com.pl",
    "depends" : ["base_vat"],
    "category" : "Generic Modules",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "cso_view.xml",
    ],
    "test": [],
    "installable": True,
    "active": False,
}
