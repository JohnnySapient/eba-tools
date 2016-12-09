# Copyright 2015 Altova GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
__copyright__ = "Copyright 2015 Altova GmbH"
__license__ = 'http://www.apache.org/licenses/LICENSE-2.0'
__version__ = '4.1'

# This script implements additional validation rules specified in the EBA XBRL Filing Rules (Version 4.1) document (https://www.eba.europa.eu/documents/10180/1181744/EBA+XBRL+Filing+Rules+v4.1.pdf)
#
# The following script parameters can be additionally specified:
#
#   max-id-length                   Issue warnings if length of id attribute values exceeds the given limit (default=50)
#   max-string-length               Issue warnings if length of fact content exceeds the given limit (default=100)
#
# Example invocations:
#
# Validate a single filing
#   raptorxmlxbrl valxbrl --script=eba_validation.py instance.xbrl
# Validate a single filing with additional options
#   raptorxmlxbrl valxbrl --script=eba_validation.py --script-param=max-id-length:10 instance.xbrl
#
# Using Altova RaptorXML+XBRL Server with XMLSpy client:
#
# 1a.   Copy eba_validation.py to the Altova RaptorXML Server script directory /etc/scripts/ (default C:\Program Files\Altova\RaptorXMLXBRLServer2016\etc\scripts\) or
# 1b.   Edit the <server.script-root-dir> tag in /etc/server_config.xml
# 2.    Start Altova RaptorXML+XBRL server
# 3.    Start Altova XMLSpy, open Tools|Manage Raptor Servers... and connect to the running server
# 4.    Create a new configuration and rename it to e.g. "EBA CHECKS"
# 5.    Select the XBRL Instance property page and then set:
# 5.1.  the 'Script' property to 'eba_validation.py'
# 5.2.  the 'Table Linkbase Namespace' property to 'http://xbrl.org/PWD/2013-05-17/table' or '##detect'
# 6.    Select the new "EBA CHECKS" configuration in Tools|Raptor Servers and Configurations
# 7.    Open a EBA instance file
# 8.    Validate instance with XML|Validate XML on Server (Ctrl+F8)


import altova_api.v2.xml as xml
import altova_api.v2.xsd as xsd
import altova_api.v2.xbrl as xbrl

def dfs(elem):
    """Returns an iterator over all elements in the given XML subtree."""
    stack = [elem]
    while stack:
        elem = stack.pop()
        yield elem
        stack.extend(elem.element_children())

# Filing syntax rules

def eba_1_4(instance,error_log):
    """EBA 1.4 - Character encoding of XBRL instance documents"""
    if instance.document.character_encoding_scheme.upper() != 'UTF-8':
        detail_error = xbrl.Error.create('XBRL instance documents SHOULD NOT use the XML standalone declaration.', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.1.4] Character encoding of XBRL instance documents.', location=instance.uri, children=[detail_error])
        error_log.report(main_error)

def eba_1_6(instance,error_log):
    """EBA 1.6 - Filing indicators"""

    # Get all filing indicators which are present in the taxonomy
    available_indicators = set()
    for table in instance.dts.tables:
        for label in table.labels(label_role='http://www.eurofiling.info/xbrl/role/filing-indicator-code'):
            available_indicators.add(label.text)

    used_indictors = {}
    indicator_facts = instance.facts.filter(xml.QName('filingIndicator','http://www.eurofiling.info/xbrl/ext/filing-indicators'))
    for indicator in indicator_facts:
        if indicator.context.entity.segment or indicator.context.scenario:
            detail_error = xbrl.Error.create('The context referenced by the filing indicator elements MUST NOT contain xbrli:segment or xbrli:scenario elements.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.1.6] Filing indicators.', location=indicator, children=[detail_error])
            error_log.report(main_error)

        if used_indictors.setdefault(indicator.normalized_value,indicator) != indicator:
            detail_error = xbrl.Error.create('Reported XBRL instances MUST contain only one filing indicator element for a given reporting unit("template").', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.1.6.1] Multiple filing indicators for the same reporting unit.', location=indicator, children=[detail_error])
            error_log.report(main_error)

        if indicator.normalized_value not in available_indicators:
            detail_error = xbrl.Error.create('The values of filing indicators MUST only be those given by the label resources with the role http://www.eurofiling.info/xbrl/role/filing-indicator-code applied to the relevant tables in the XBRL taxonomy4 for that reporting module (entry point). Filing indicator values must be formatted correctly (for example including any underscore characters).', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.1.6.3] Filing indicator codes.', location=indicator, children=[detail_error])
            error_log.report(main_error)

def eba_1_13(instance,error_log):
    """EBA 1.13 - Standalone Document Declaration"""
    if instance.document.standalone is not None:
        detail_error = xbrl.Error.create('XBRL instance documents MUST use "UTF-8" encoding. [GFM11, p. 11]', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.1.13] Standalone Document Declaration.', location=instance.uri, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
        error_log.report(main_error)

def eba_1_14(instance,error_log):
    """EBA 1.14 - @xsd:schemaLocation and @xsd:noNamespaceSchemaLocation"""
    attr = instance.document_element.find_attribute(xml.QName('schemaLocation','http://www.w3.org/2001/XMLSchema-instance'))
    if not attr:
        attr = instance.document_element.find_attribute(xml.QName('noNamespaceSchemaLocation','http://www.w3.org/2001/XMLSchema-instance'))
    if attr:
        detail_error = xbrl.Error.create('@xsd:schemaLocation or @xsd:noNamespaceSchemaLocation MUST NOT be used.', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.1.14] @xsd:schemaLocation and @xsd:noNamespaceSchemaLocation.', location=attr, children=[detail_error])
        error_log.report(main_error)

def eba_1_15(instance,options,error_log):
    """EBA 1.15 — XInclude"""
    # --xinclude option switched off by default in RaptorXML+XBRL
    if options.get('xinclude') == True:
        detail_error1 = xbrl.Error.create('XBRL instance documents MUST NOT use the XInclude specification (xi:include element).', severity=xml.ErrorSeverity.INFO)
        detail_error2 = xbrl.Error.create('Hint: Disable XInclude support with the --xinclude=false option.', severity=xml.ErrorSeverity.OTHER)
        main_error = xbrl.Error.create('[EBA.1.15] XInclude.', location=instance.uri,children=[detail_error1,detail_error2])
        error_log.report(main_error)

# Instance syntax rules

def eba_2_1(instance,error_log):
    """EBA 2.1 - The existence of xml:base is not permitted"""
    for elem in dfs(instance.document_element):
        xml_base_attr = elem.find_attribute(xml.QName('base','http://www.w3.org/XML/1998/namespace'))
        if xml_base_attr:
            detail_error = xbrl.Error.create('The attribute @xml:base MUST NOT appear in any instance document. [EFM13, p. 6-7].', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.1] The existence of {xml_base} is not permitted.', xml_base=xml_base_attr, children=[detail_error])
            error_log.report(main_error)

def eba_2_2(instance,error_log):
    """EBA 2.2 - The absolute URL has to be stated for the link:schemaRef element"""
    if not next(instance.schema_refs).xlink_href.startswith('http://'):
        detail_error = xbrl.Error.create('The link:schemaRef element in submitted instances MUST resolve to the full published entry point URL (absolute URL).', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.2.2] The absolute URL has to be stated for the {schemaRef} element.', schemaRef=schema_refs[0], children=[detail_error])
        error_log.report(main_error)

def eba_2_3(instance,error_log):
    """EBA 2.3 - Only one link:schemaRef element is allowed per instance document"""
    for schema_ref in list(instance.schema_refs)[1:]:
        detail_error = xbrl.Error.create('Any reported XBRL instance document MUST contain only one xbrli:xbrl/link:schemaRef element.', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.2.3] Only one {schemaRef} element is allowed per instance document.', schemaRef=schema_ref, children=[detail_error])
        error_log.report(main_error)

def eba_2_4(instance,error_log):
    """EBA 2.4 - The use of link:linkbaseRef elements is not permitted"""
    for linkbase_ref in instance.linkbase_refs:
        detail_error = xbrl.Error.create('Reference from an instance to the taxonomy MUST only be by means of the link:schemaRef element. The element link:linkbaseRef MUST NOT be used in any instance document.', severity=xml.ErrorSeverity.INFO)
        main_error = xbrl.Error.create('[EBA.2.4] The use of {linkbaseRef} element is not permitted.', linkbaseRef=linkbase_ref, children=[detail_error])
        error_log.report(main_error)

def eba_2_25(instance,error_log):
    """EBA 2.25 - XBRL footnotes are ignored by EBA"""
    for link in instance.footnote_links:
        for footnote in link.resources:
            detail_error = xbrl.Error.create('Relevant business data MUST only be contained in contexts, units, schemaRef and facts. A footnote MUST not have any impact on the regulatory content of a report.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.25] XBRL {footnote} are ignored by EBA.', footnote=footnote, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

# Context related rules

def eba_2_6(instance,params,error_log):
    """EBA 2.6 - The length of the @id attribute should be limited to the necessary characters"""
    max_id_length = int(params.get('max-id-length',50))
    for context in instance.contexts:
        if len(context.id) > max_id_length:
            id_attr = context.element.find_attribute('id')
            detail_error = xbrl.Error.create('Semantics SHOULD NOT be expressed in the xbrli:context/@id attribute. The values of each @id attribute SHOULD be as short as possible.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.6] The length of the {id} attribute should be limited to the necessary characters.', id=id_attr, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_2_7(instance,error_log):
    """EBA 2.7 - No unused or duplicated xbrli:context nodes"""
    aspects_map = {}
    for context in instance.contexts:
        # Check for unused contexts
        if not instance.facts.filter(context):
            detail_error = xbrl.Error.create('Unused xbrli:context nodes SHOULD NOT be present in the instance. [FRIS04]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.7] No unused or duplicated {context} nodes.', context=context.element, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

        # Check for duplicated contexts
        duplicates = aspects_map.setdefault(xbrl.ConstraintSet(context),[])
        if duplicates:
            detail_error1 = xbrl.Error.create('An instance document SHOULD NOT contain duplicated context, unless required for technical reasons, e.g. to support XBRL streaming.', severity=xml.ErrorSeverity.INFO)
            detail_error2 = xbrl.Error.create('Context {context} is a duplicate of context {context2}', context=context, context2=duplicates[0], severity=xml.ErrorSeverity.OTHER)
            main_error = xbrl.Error.create('[EBA.2.7] No unused or duplicated {context} nodes.', context=context.element, children=[detail_error1,detail_error2], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)
        else:
            duplicates.append(context)

def eba_2_9(instance,error_log):
    """EBA 2.9 - Single reporter per instance"""
    single_identifier = next(instance.contexts).entity_identifier_aspect_value
    for context in instance.contexts:
        if context.entity_identifier_aspect_value != single_identifier:
            detail_error = xbrl.Error.create('All xbrli:identifier content and @scheme attributes in an instance MUST be identical. [EFM13, p. 6-8]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.9] Single reporter per instance.', location=context.entity.identifier, children=[detail_error])
            error_log.report(main_error)

def eba_2_10(instance,error_log):
    """EBA 2.10 - The xbrli:period date elements reported must be valid"""
    for context in instance.contexts:
        period = context.period
        if period.instant and (period.instant.value.tzinfo or period.instant.element.member_type_definition.name != "date"):
            detail_error = xbrl.Error.create('All xbrli:period date elements MUST be valid against the xs:date data type, and reported without a timezone. [GFM11, p. 16]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.10] The {period} date elements reported must be valid.', period=context.period, children=[detail_error])
            error_log.report(main_error)

def eba_2_11(instance,error_log):
    """EBA 2.11 - The existence of xbrli:forever is not permitted"""
    for context in instance.contexts:
        if context.period.is_forever():
            detail_error = xbrl.Error.create('The element ‘xbrli:forever’ MUST NOT be used. [GFM11, p. 19]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.11] The existence of {forever} is not permitted.', forever=context.period.forever, children=[detail_error])
            error_log.report(main_error)

def eba_2_13(instance,error_log):
    """EBA 2.13 - XBRL period consistency"""
    single_period = next(instance.contexts).period_aspect_value
    for context in instance.contexts:
        if not context.period.is_instant() or context.period_aspect_value != single_period:
            detail_error = xbrl.Error.create('All xbrl periods in a report instance MUST refer to the (same) reference date instant. All xbrl periods MUST be instants.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.13] XBRL {period} consistency.', period=context.period, children=[detail_error])
            error_log.report(main_error)

def eba_2_14(instance,error_log):
    """EBA 2.14 - The existence of xbrli:segment is not permitted"""
    for context in instance.contexts:
        if context.entity.segment:
            detail_error = xbrl.Error.create('xbrli:segment elements MUST NOT be used.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.14] The existence of {segment} is not permitted.', segment=context.entity.segment, children=[detail_error])
            error_log.report(main_error)

def eba_2_15(instance,error_log):
    """EBA 2.15 - Restrictions on the use of the xbrli:scenario element"""
    for context in instance.contexts:
        if context.scenario and next(context.scenario.non_xdt_child_elements,None):
            detail_error = xbrl.Error.create('If an xbrli:scenario element appears in a xbrli:context, then its children MUST only be one or more xbrldi:explicitMember and/or xbrldi:typedMember elements, and MUST NOT contain any other content. [EFM13, p. 6-8].', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.15] Restrictions on the use of the {scenario} element.', scenario=context.scenario, children=[detail_error])
            error_log.report(main_error)

# Fact related rules

def eba_2_16(instance,error_log):
    """EBA 2.16 - Duplicate (Redundant/Inconsistent) facts"""
    # Taking advantage of disallowed duplicate contexts and units. Otherwise one would need to hash by the aspect values.
    for aspect in instance.facts.concept_aspect_values():
        if isinstance(aspect.concept,xbrl.taxonomy.Item) and (aspect.concept.target_namespace != "http://www.eurofiling.info/xbrl/ext/filing-indicators" or aspect.concept.name != "filingIndicator"):
            duplicate_facts = {}
            for fact in instance.facts.filter(aspect.concept):
                key = (fact.context,fact.xml_lang)
                if duplicate_facts.setdefault(key,fact) != fact:
                    duplicate_fact = duplicate_facts[key]
                    if fact.unit == duplicate_fact.unit:
                        detail_error = xbrl.Error.create('Instances MUST NOT contain duplicate business facts. [FRIS04],[EFM13, p. 6-10]', severity=xml.ErrorSeverity.INFO)
                        main_error = xbrl.Error.create('[EBA.2.16] Duplicate (Redundant/Inconsistent) facts {fact} and {fact2}.', fact=fact, fact2=duplicate_fact, children=[detail_error])
                        error_log.report(main_error)
                    else:
                        detail_error = xbrl.Error.create('Instances MUST NOT contain business facts which would be duplicates were their units not different.', severity=xml.ErrorSeverity.INFO)
                        main_error = xbrl.Error.create('[EBA.2.16.1] No multi-unit facts {fact} and {fact2}.', fact=fact, fact2=duplicate_fact, children=[detail_error])
                        error_log.report(main_error)

def eba_2_17(instance,error_log):
    """EBA 2.17 - The use of the @precision attribute is not permitted"""
    for fact in instance.child_items:
        if fact.precision:
            precision_attr = fact.element.find_attribute('precision')
            detail_error = xbrl.Error.create('@decimals MUST be used as the only means for expressing precision on a fact. [FRIS 2.8.1.1, EFM13, p.6-12].', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.17] The use of the {precision} attribute is not permitted.', precision=precision_attr, children=[detail_error])
            error_log.report(main_error)

def eba_2_19(instance,error_log):
    """EBA 2.19 - Guidance on use of zeros and non-reported data"""
    for fact in instance.child_items:
        if fact.xsi_nil:
            xsi_nil_attr = fact.element.find_attribute(('nil','http://www.w3.org/2001/XMLSchema-instance'))
            detail_error = xbrl.Error.create('The {xsi_nil} attribute MUST NOT be used in the instance.', xsi_nil=xsi_nil_attr, severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.19] Guidance on use of zeros and non-reported data.', location=fact, children=[detail_error])
            error_log.report(main_error)

# Unit related rules

def eba_2_21(instance,error_log):
    """EBA 2.21 - Duplicates of xbrli:xbrl/xbrli:unit"""
    aspects_map = {}
    for unit in instance.units:
        duplicates = aspects_map.setdefault(xbrl.ConstraintSet(unit),[])
        if duplicates:
            detail_error1 = xbrl.Error.create('An XBRL instance SHOULD NOT, in general, contain duplicated units, unless required for technical reasons, e.g. to support XBRL streaming.', severity=xml.ErrorSeverity.INFO)
            detail_error2 = xbrl.Error.create('Unit {unit} is a duplicate of unit {unit2}', unit=unit, unit2=duplicates[0], severity=xml.ErrorSeverity.OTHER)
            main_error = xbrl.Error.create('[EBA.2.21] Duplicates of xbrli:xbrl/xbrli:unit.', location=unit.element, children=[detail_error1,detail_error2], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)
        else:
            duplicates.append(unit)

def eba_2_22(instance,error_log):
    """EBA 2.22 - Unused xbrli:xbrl/xbrli:unit"""
    for unit in instance.units:
        if not instance.facts.filter(unit):
            detail_error = xbrl.Error.create('An XBRL instance SHOULD NOT contain unused xbrli:unit nodes. [FRIS04]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.2.22] Unused xbrli:xbrl/xbrli:unit.', location=unit, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_1(instance,error_log):
    """EBA 3.1 - Choice of Currency for Monetary facts"""
    eba_dim_CCA = instance.dts.resolve_concept(xml.QName('CCA','http://www.eba.europa.eu/xbrl/crr/dict/dim'))
    eba_dim_CUS = instance.dts.resolve_concept(xml.QName('CUS','http://www.eba.europa.eu/xbrl/crr/dict/dim'))
    eba_CA_x1 = instance.dts.resolve_concept(xml.QName('x1','http://www.eba.europa.eu/xbrl/crr/dict/dom/CA'))

    constraints = xbrl.ConstraintSet()
    constraints[eba_dim_CCA] = eba_CA_x1
    denomination_facts = instance.facts.filter(constraints)
    for fact in denomination_facts:
        if fact.concept.is_monetary():
            aspect_values = fact.aspect_values
            currency = aspect_values.get(eba_dim_CUS,None)
            if currency and currency.value.name != aspect_values[xbrl.Aspect.UNIT].iso4217_currency:
                detail_error = xbrl.Error.create('For facts falling under point (b), whose context also includes the dimension “Currency with significant liabilities” (CUS), the currency of the fact (i.e. unit) MUST be consistent with the value given for this dimension.', severity=xml.ErrorSeverity.INFO)
                main_error = xbrl.Error.create('[EBA.3.1] Choice of Currency for Monetary fact {fact}.', fact=fact, children=[detail_error])
                error_log.report(main_error)

    monetary_units = []
    for unit in instance.units:
        if unit.aspect_value.is_monetary():
            monetary_units.append(unit)
    # Optimization: Only do the single currency check if more than one monetary unit is present
    if len(monetary_units) > 1:
        single_unit = None
        for fact in instance.child_items - denomination_facts:
            if fact.concept.is_monetary():
                if single_unit is None:
                    single_unit = fact.unit
                elif fact.unit != single_unit:
                    detail_error = xbrl.Error.create('An instance MUST express all monetary facts which do not fall under point (b) using a single currency.', severity=xml.ErrorSeverity.INFO)
                    main_error = xbrl.Error.create('[EBA.3.1] Choice of Currency for Monetary fact {fact}.', fact=fact, children=[detail_error])
                    error_log.report(main_error)

def eba_3_2(instance,error_log):
    """EBA 3.2 - Non-monetary numeric units"""
    for fact in instance.child_items:
        if fact.concept.is_numeric() and not fact.concept.is_monetary():
            if not fact.unit.aspect_value.is_pure():
                detail_error = xbrl.Error.create('An instance MUST express its non-monetary numeric values using the “pure” unit, a unit element with a single measure element as its only child. The local part of the measure MUST be "pure" and the namespace prefix MUST resolve to the namespace: http://www.xbrl.org/2003/instance.', severity=xml.ErrorSeverity.INFO)
                main_error = xbrl.Error.create('[EBA.3.2] Non-monetary numeric units.', location=fact, children=[detail_error])
                error_log.report(main_error)

def eba_3_4(instance,error_log):
    """EBA 3.4 - Unused namespace prefixes"""
    used_prefixes = set()
    for elem in dfs(instance.document_element):
        used_prefixes.add(elem.prefix)
        val = elem.schema_actual_value
        if isinstance(val,xsd.QName):
            used_prefixes.add(val.prefix)
        for attr in elem.attributes:
            used_prefixes.add(attr.prefix)
            val = attr.schema_actual_value
            if isinstance(val,xsd.QName):
                used_prefixes.add(val.prefix)

    for nsattr in instance.document_element.namespace_attributes:
        if nsattr.local_name != 'xmlns' and nsattr.local_name not in used_prefixes:
            detail_error = xbrl.Error.create('Namespace prefixes that are not used SHOULD not be declared in the instance document. [FRIS04]', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.4] Unused namespace prefix {prefix}.', prefix=nsattr, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_5(instance,error_log):
    """EBA 3.5 - Re-use of canonical namespace prefixes"""
    namespace_bindings = {}
    for schema in instance.dts.taxonomy_schemas:
        for nsattr in schema.element.namespace_attributes:
            if nsattr.local_name != 'xmlns' and nsattr.normalized_value == schema.target_namespace:
                namespace_bindings[schema.target_namespace] = nsattr.local_name
                break

    for nsattr in instance.document_element.namespace_attributes:
        if nsattr.local_name != 'xmlns' and nsattr.local_name != namespace_bindings.get(nsattr.normalized_value,nsattr.local_name):
                detail_error = xbrl.Error.create('Namespace prefixes, where used in instance documents, SHOULD mirror the namespace prefixes as defined by their schema author(s). [FRIS04]', severity=xml.ErrorSeverity.INFO)
                main_error = xbrl.Error.create('[EBA.3.5] Re-use of canonical namespace prefix {prefix}.', prefix=nsattr, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
                error_log.report(main_error)

def eba_3_6(instance,error_log):
    """EBA 3.6 - LEI and other entity codes"""
    for context in instance.contexts:
        if context.entity_identifier_aspect_value.scheme == 'http://standard.iso.org/iso/17442':
            detail_error = xbrl.Error.create('Producers of instance documents are encouraged to switch as quickly as possible to producing the correct form “http://standards.iso.org/iso/17442”.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.6] LEI and other entity codes.', location=context.entity.identifier, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_7(instance,error_log):
    """EBA 3.7 - Unused @id attribute on facts"""
    # Inside the instance facts can only be referenced by id from footnote locators
    used_ids = set()
    for footnote_link in instance.footnote_links:
        for loc in footnote_link.locators:
            fragment = loc.xlink_href.split('#')[-1]
            # Check for short-hand xpointer notation
            if '(' not in fragment:
                used_ids.add(fragment)

    for fact in instance.child_items:
        if fact.id and fact.id not in used_ids:
            id_attr = fact.element.find_attribute('id')
            detail_error = xbrl.Error.create('The instance SHOULD NOT include unused @id attributes on facts.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.7] Unused {id} attribute on fact.', id=id_attr, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_8(instance,params,error_log):
    """EBA 3.8 - Length of strings in instance"""
    max_string_length = int(params.get('max-string-length',100))
    for fact in instance.child_items:
        val = fact.element.schema_actual_value
        if isinstance(val,xsd.string) and len(val.value) > max_string_length:
            detail_error = xbrl.Error.create('The values of each string SHOULD be as short as possible.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.8] Length of strings in instance.', location=fact, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_9(instance,error_log):
    """EBA 3.9 - Namespace prefix declarations restricted to the document element"""
    elements = dfs(instance.document_element)
    next(elements)  # skip document element
    for elem in elements:
        for nsattr in elem.namespace_attributes:
            detail_error = xbrl.Error.create('Namespace prefixes declarations SHOULD be restricted to the document element.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.9] Namespace prefix declaration {prefix} restricted to the document element.', prefix=nsattr, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def eba_3_10(instance,error_log):
    """EBA 3.10 - Avoid multiple prefix declarations for the same namespace"""
    used_namespaces = {}
    for nsattr in instance.document_element.namespace_attributes:
        if used_namespaces.setdefault(nsattr.normalized_value,nsattr) != nsattr:
            detail_error = xbrl.Error.create('Namespaces used in the document SHOULD be associated to a single namespace prefix.', severity=xml.ErrorSeverity.INFO)
            main_error = xbrl.Error.create('[EBA.3.10] Avoid multiple prefix declarations {prefix} and {prefix2} for the same namespace {namespace}.', prefix=nsattr, prefix2=used_namespaces[nsattr.normalized_value], namespace=nsattr.normalized_value, children=[detail_error], severity=xml.ErrorSeverity.WARNING)
            error_log.report(main_error)

def check_eba_filing_rules(job, instance):
    """Check additional EBA filing rules"""
    catalog = job.catalog
    params = job.script_params
    error_log = job.error_log

    # 1. Filing syntax rules
    # 1.1 - Filing naming
    # Needs to be implemented on a per authority basis!
    # 1.4 - Character encoding of XBRL instance documents
    eba_1_4(instance,error_log)
    # 1.5 - Taxonomy entry point selection
    # Needs to be implemented on a per authority basis!
    # 1.6 - Filing indicators
    eba_1_6(instance,error_log)
    # 1.7 - Implication of no facts for an indicated template
    # Cannot be checked automatically!

    # 1.10 - Valid according to the defined business rules
    # TODO: Currently not possible to accesss the formula assertion results in the Python API
    # 1.11 - Taxonomy extensions by reporters
    # Needs to be implemented on a per authority basis!
    # 1.12 - Completeness of the instance
    # Cannot be checked automatically!
    # 1.13 - Standalone Document Declaration
    eba_1_13(instance,error_log)
    # 1.14 - @xsd:schemaLocation and @xsd:noNamespaceSchemaLocation
    eba_1_14(instance,error_log)
    # 1.15 - XInclude
    eba_1_15(instance,job.options,error_log)

    # 2. Instance syntax rules
    # 2.1 — The existence of xml:base is not permitted
    eba_2_1(instance,error_log)
    # 2.2 - The absolute URL has to be stated for the link:schemaRef element
    eba_2_2(instance,error_log)
    # 2.3 - Only one link:schemaRef element is allowed per instance document
    eba_2_3(instance,error_log)
    # 2.4 - The use of link:linkbaseRef elements is not permitted
    eba_2_4(instance,error_log)
    # 2.5 - XML comments and documentation are ignored by EBA
    # Cannot be checked automatically!
    # 2.25 - XBRL footnotes are ignored by EBA
    eba_2_25(instance,error_log)

    # Context related rules

    # 2.6 - The length of the @id attribute should be limited to the necessary characters
    eba_2_6(instance,params,error_log)
    # 2.7 - No unused or duplicated xbrli:context nodes
    eba_2_7(instance,error_log)
    # 2.8 — Identification of the reporting entity
    # Cannot be checked automatically!
    # 2.9 - Single reporter per instance
    eba_2_9(instance,error_log)
    # 2.10 - The xbrli:period date elements reported must be valid
    eba_2_10(instance,error_log)
    # 2.11 - The existence of xbrli:forever is not permitted
    eba_2_11(instance,error_log)
    # 2.13 - XBRL period consistency
    eba_2_13(instance,error_log)
    # 2.14 - The existence of xbrli:segment is not permitted
    eba_2_14(instance,error_log)
    # 2.15 - Restrictions on the use of the xbrli:scenario element
    eba_2_15(instance,error_log)

    # Fact related rules

    # 2.16 - Duplicate (Redundant/Inconsistent) facts
    eba_2_16(instance,error_log)
    # 2.17 - The use of the @precision attribute is not permitted
    eba_2_17(instance,error_log)
    # 2.18 - Interpretation of the @decimals attribute
    # Cannot be checked automatically!
    # 2.19 - Guidance on use of zeros and non-reported data
    eba_2_19(instance,error_log)
    # 2.20 - Information on the use of the xml:lang attribute
    # Cannot be checked automatically!

    # Unit related rules

    # 2.21 - Duplicates of xbrli:xbrl/xbrli:unit
    eba_2_21(instance,error_log)
    # 2.22 - Unused xbrli:xbrl/xbrli:unit
    eba_2_22(instance,error_log)
    # 2.23 - Reference xbrli:unit to XBRL International Unit Type Registry (UTR)
    # Already checked by the XBRL validator
    # 2.24 - Report of the actual physical value of monetary items (see also 3.3)
    # This should be already checked by XBRL 2.1 validation as monetary fact items must only reference units with a single ISO 4217 currency measure.
    # 3.1 - Choice of Currency for Monetary facts
    eba_3_1(instance,error_log)
    # 3.2 - Non-monetary numeric units
    eba_3_2(instance,error_log)
    # 3.3 - Decimal representation
    # Cannot be checked automatically!

    # 3. Additional Guidance

    # 3.4 Unused namespace prefixes
    eba_3_4(instance,error_log)
    # 3.5 Re-use of canonical namespace prefixes
    eba_3_5(instance,error_log)
    # 3.6 - LEI and other entity codes
    eba_3_6(instance,error_log)
    # 3.7 - Unused @id attribute on facts
    eba_3_7(instance,error_log)
    # 3.8 - Length of strings in instance
    eba_3_8(instance,params,error_log)
    # 3.9 - Namespace prefix declarations restricted to the document element
    eba_3_9(instance,error_log)
    # 3.10 - Avoid multiple prefix declarations for the same namespace
    eba_3_10(instance,error_log)

def on_xbrl_finished_dts(job, dts):
    # EBA 2.23 - Reference xbrli:unit to XBRL International Unit Type Registry (UTR)
    job.options['utr'] = True   # Enable UTR validation

# Main entry point, will be called by RaptorXML after the XBRL instance validation job has finished
def on_xbrl_finished(job, instance):
    # instance object will be None if XBRL 2.1 validation was not successful
    if instance is not None:
        check_eba_filing_rules(job, instance)
    else:
        # EBA 1.9 - Valid XML-XBRL.
        xbrl_errors = [xbrl.Error.create('Instance documents MUST be XBRL 2.1 and XBRL Dimensions 1.0 valid. [EFM11, p. 6-8]', severity=xml.ErrorSeverity.INFO)]
        xbrl_errors.extend(list(job.error_log.errors))
        main_error = xbrl.Error.create('[EBA.1.9] Valid XML-XBRL.', children=xbrl_errors)
        job.error_log.clear()
        job.error_log.report(main_error)
