<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<xsl:template match="/">
		<KEDU wersja_schematu="1" xmlns="http://www.zus.pl/2013/KEDU_4"
		xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
		xsi:schemaLocation="http://www.zus.pl/bip/pliki/kedu_4.xsd">
			<naglowek.KEDU>
				<program>
					<producent>Asseco Poland SA</producent>
					<symbol>Płatnik</symbol>
					<wersja>901001</wersja>
				</program>
			</naglowek.KEDU>
			<xsl:if test="report/employer/ZUA_id != ''">
			<ZUSZUA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/ZUA_id" />
				</xsl:attribute>
				<I>
					<xsl:if test="report/employee/I01 != ''">
						<p1><xsl:value-of select="report/employee/I01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/I02 != ''">
						<p2><xsl:value-of select="report/employee/I02"/></p2>
					</xsl:if>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<III>
					<xsl:if test="report/employee/III01 != ''">
						<p1><xsl:value-of select="report/employee/III01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/III03 != ''">
						<p3><xsl:value-of select="report/employee/III03"/></p3>
						<p4><xsl:value-of select="report/employee/III04"/></p4>
					</xsl:if>
					<p5><xsl:value-of select="report/employee/III05"/></p5>
					<p6><xsl:value-of select="report/employee/III06"/></p6>
					<p7><xsl:value-of select="report/employee/III07"/></p7>
				</III>
				<IV>
					<xsl:if test="report/employee/IV01 != ''">
						<p1><xsl:value-of select="report/employee/IV01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/IV02 != ''">
						<p2><xsl:value-of select="report/employee/IV02"/></p2>
					</xsl:if>
					<p3><xsl:value-of select="report/employee/IV03"/></p3>
					<p4><xsl:value-of select="report/employee/IV04"/></p4>
				</IV>
				<V>
					<p1>
						<p1><xsl:value-of select="report/employee/V01_1"/></p1>
						<p2><xsl:value-of select="report/employee/V01_2"/></p2>
						<p3><xsl:value-of select="report/employee/V01_3"/></p3>
					</p1>
				</V>
				<VI>
					<p1><xsl:value-of select="report/employee/ZUA_VI01"/></p1>
					<p2><xsl:value-of select="report/employee/ZUA_VI02"/></p2>
					<p3><xsl:value-of select="report/employee/ZUA_VI03"/></p3>
					<p4><xsl:value-of select="report/employee/ZUA_VI04"/></p4>
					<p5><xsl:value-of select="report/employee/ZUA_VI05"/></p5>
				</VI>
				<VII>
					<p1><xsl:value-of select="report/employee/VII01"/></p1>
					<p2><xsl:value-of select="report/employee/VII02"/></p2>
				</VII>
				<xsl:if test="report/employee/XI02 != ''">
				<XI>
					<xsl:if test="report/employee/XI01 != ''">
						<p1><xsl:value-of select="report/employee/XI01"/></p1>
					</xsl:if>
					<p2><xsl:value-of select="report/employee/XI02"/></p2>
					<p3><xsl:value-of select="report/employee/XI03"/></p3>
					<p4><xsl:value-of select="report/employee/XI04"/></p4>
					<p5><xsl:value-of select="report/employee/XI05"/></p5>
					<xsl:if test="report/employee/XI06 != ''">
						<p6><xsl:value-of select="report/employee/XI06"/></p6>
					</xsl:if>
					<xsl:if test="report/employee/XI08 != ''">
						<p8><xsl:value-of select="report/employee/XI08"/></p8>
					</xsl:if>
				</XI>
				</xsl:if>
				<xsl:if test="report/employee/XII02 != ''">
				<XII>
					<xsl:if test="report/employee/XII01 != ''">
						<p1><xsl:value-of select="report/employee/XII01"/></p1>
					</xsl:if>
					<p2><xsl:value-of select="report/employee/XII02"/></p2>
					<p3><xsl:value-of select="report/employee/XII03"/></p3>
					<p4><xsl:value-of select="report/employee/XII04"/></p4>
					<p5><xsl:value-of select="report/employee/XII05"/></p5>
					<xsl:if test="report/employee/XII06 != ''">
						<p6><xsl:value-of select="report/employee/XII06"/></p6>
					</xsl:if>
					<xsl:if test="report/employee/XII08 != ''">
						<p8><xsl:value-of select="report/employee/XII08"/></p8>
					</xsl:if>
				</XII>
				</xsl:if>
				<xsl:if test="report/employee/XIII02 != ''">
				<XIII>
					<xsl:if test="report/employee/XIII01 != ''">
						<p1><xsl:value-of select="report/employee/XIII01"/></p1>
					</xsl:if>
					<p2><xsl:value-of select="report/employee/XIII02"/></p2>
					<p3><xsl:value-of select="report/employee/XIII03"/></p3>
					<p4><xsl:value-of select="report/employee/XIII04"/></p4>
					<p5><xsl:value-of select="report/employee/XIII05"/></p5>
					<xsl:if test="report/employee/XIII06 != ''">
						<p6><xsl:value-of select="report/employee/XIII06"/></p6>
					</xsl:if>
					<xsl:if test="report/employee/XIII08 != ''">
						<p8><xsl:value-of select="report/employee/XIII08"/></p8>
					</xsl:if>
				</XIII>
				</xsl:if>
				<XIV>
					<p1><xsl:value-of select="report/employer/XIV01"/></p1>
				</XIV>
			</ZUSZUA>
			</xsl:if>
			
			<xsl:if test="report/employer/ZWUA_id != ''">
			<ZUSZWUA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/ZWUA_id" />
				</xsl:attribute>
				<I>
					<xsl:if test="report/employee/I01 != ''">
						<p1><xsl:value-of select="report/employee/I01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/I02 != ''">
						<p2><xsl:value-of select="report/employee/I02"/></p2>
					</xsl:if>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<III>
					<xsl:if test="report/employee/III01 != ''">
						<p1><xsl:value-of select="report/employee/III01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/III03 != ''">
						<p3><xsl:value-of select="report/employee/III03"/></p3>
						<p4><xsl:value-of select="report/employee/III04"/></p4>
					</xsl:if>
					<p5><xsl:value-of select="report/employee/III05"/></p5>
					<p6><xsl:value-of select="report/employee/III06"/></p6>
					<p7><xsl:value-of select="report/employee/III07"/></p7>
				</III>
				<IV>
					<p1>
						<p1><xsl:value-of select="report/employee/ZWUA_IV01_1"/></p1>
						<p2><xsl:value-of select="report/employee/ZWUA_IV01_2"/></p2>
						<p3><xsl:value-of select="report/employee/ZWUA_IV01_3"/></p3>
					</p1>
					<p2><xsl:value-of select="report/employee/ZWUA_IV02"/></p2>
					<p3><xsl:value-of select="report/employee/ZWUA_IV03"/></p3>
				</IV>
				<V>
					<p1><xsl:value-of select="report/employer/XIV01"/></p1>
				</V>
			</ZUSZWUA>
			</xsl:if>
	
			<xsl:if test="report/employer/ZZA_id != ''">
			<ZUSZZA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/ZZA_id" />
				</xsl:attribute>
				<I>
					<xsl:if test="report/employee/I01 != ''">
						<p1><xsl:value-of select="report/employee/I01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/I02 != ''">
						<p2><xsl:value-of select="report/employee/I02"/></p2>
					</xsl:if>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<III>
					<xsl:if test="report/employee/III01 != ''">
						<p1><xsl:value-of select="report/employee/III01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/III03 != ''">
						<p3><xsl:value-of select="report/employee/III03"/></p3>
						<p4><xsl:value-of select="report/employee/III04"/></p4>
					</xsl:if>
					<p5><xsl:value-of select="report/employee/III05"/></p5>
					<p6><xsl:value-of select="report/employee/III06"/></p6>
					<p7><xsl:value-of select="report/employee/III07"/></p7>
				</III>
				<IV>
					<xsl:if test="report/employee/IV01 != ''">
						<p1><xsl:value-of select="report/employee/IV01"/></p1>
					</xsl:if>
					<xsl:if test="report/employee/IV02 != ''">
						<p2><xsl:value-of select="report/employee/IV02"/></p2>
					</xsl:if>
					<p3><xsl:value-of select="report/employee/IV03"/></p3>
					<p4><xsl:value-of select="report/employee/IV04"/></p4>
				</IV>
				<V>
					<p1>
						<p1><xsl:value-of select="report/employee/V01_1"/></p1>
						<p2><xsl:value-of select="report/employee/V01_2"/></p2>
						<p3><xsl:value-of select="report/employee/V01_3"/></p3>
					</p1>
				</V>
				<VI>
					<p1><xsl:value-of select="report/employee/VII01"/></p1>
					<p2><xsl:value-of select="report/employee/VII02"/></p2>
				</VI>
				<xsl:if test="report/employee/XI01 != ''">
				<VIII>
					<p1><xsl:value-of select="report/employee/XI01"/></p1>
					<p2><xsl:value-of select="report/employee/XI02"/></p2>
					<p3><xsl:value-of select="report/employee/XI03"/></p3>
					<p4><xsl:value-of select="report/employee/XI04"/></p4>
					<p5><xsl:value-of select="report/employee/XI05"/></p5>
					<xsl:if test="report/employee/XI06 != ''">
						<p6><xsl:value-of select="report/employee/XI06"/></p6>
					</xsl:if>
				</VIII>
				</xsl:if>
				<xsl:if test="report/employee/XII01 != ''">
				<IX>
					<p1><xsl:value-of select="report/employee/XII01"/></p1>
					<p2><xsl:value-of select="report/employee/XII02"/></p2>
					<p3><xsl:value-of select="report/employee/XII03"/></p3>
					<p4><xsl:value-of select="report/employee/XII04"/></p4>
					<p5><xsl:value-of select="report/employee/XII05"/></p5>
					<xsl:if test="report/employee/XII06 != ''">
						<p6><xsl:value-of select="report/employee/XII06"/></p6>
					</xsl:if>
				</IX>
				</xsl:if>
				<xsl:if test="report/employee/XIII01 != ''">
				<X>
					<p1><xsl:value-of select="report/employee/XIII01"/></p1>
					<p2><xsl:value-of select="report/employee/XIII02"/></p2>
					<p3><xsl:value-of select="report/employee/XIII03"/></p3>
					<p4><xsl:value-of select="report/employee/XIII04"/></p4>
					<p5><xsl:value-of select="report/employee/XIII05"/></p5>
					<xsl:if test="report/employee/XIII06 != ''">
						<p6><xsl:value-of select="report/employee/XIII06"/></p6>
					</xsl:if>
				</X>
				</xsl:if>
				<XI>
					<p1><xsl:value-of select="report/employer/XIV01"/></p1>
				</XI>
			</ZUSZZA>
			</xsl:if>
		</KEDU>
	</xsl:template>
</xsl:stylesheet>