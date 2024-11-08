# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from doc_info_layer.CharterReports import InformacionGeneral, CapitalSocial, InformacionAdministracion, RepresentanteLegal, InformacionNotario

# Determines the sections that will be extracted from the document. The order is preserved for the final report
report_sections = [
    "general_information",
    "shareholders",
    "administration",
    "legal_representative",
    "notary_information"
]

# Determines to which object each section is mapped
info_to_output_mapping = {
    report_sections[0]: InformacionGeneral,
    report_sections[1]: CapitalSocial,
    report_sections[2]: InformacionAdministracion,
    report_sections[3]: RepresentanteLegal,
    report_sections[4]: InformacionNotario
}