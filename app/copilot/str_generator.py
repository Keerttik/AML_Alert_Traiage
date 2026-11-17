from typing import Dict, Any, List

def generate_draft_str(context: Dict[str, Any], rationale_reasons: List[str], language: str = "en") -> str:
    """Generates a standard regulatory 5W1H Suspicious Transaction Report (STR) narrative draft

    with strict source citations and required audit disclaimers in English, Spanish, French, or Arabic.
    """
    customer = context.get("customer", {})
    alert = context.get("alert", {})
    transactions = context.get("transactions", [])
    flagged_txns = [t for t in transactions if t.get("flagged")] or transactions

    total_amount = sum(t.get("amount", 0) for t in flagged_txns)
    dates = sorted([t.get("date", "") for t in flagged_txns if t.get("date")])
    date_start = dates[0] if dates else "N/A"
    date_end = dates[-1] if dates else "N/A"

    channels = list({t.get("channel", "Unknown") for t in flagged_txns})
    counterparties = list({t.get("counterparty") for t in flagged_txns if t.get("counterparty")})
    reasons_text = "\n".join([f"  - {r}" for r in rationale_reasons]) if rationale_reasons else "  - Unexplained deviation from profile"

    lang = (language or "en").lower()

    if lang == "es":
        return f"""[BORRADOR — REQUIERE REVISIÓN DEL ANALISTA ANTES DEL ENVÍO]
================================================================================
REPORTE DE OPERACIONES SOSPECHOSAS (ROS) — NARRATIVA REGULATORIA
Referencia de Alerta: {alert.get('alert_id', 'N/A')} [Regla: {alert.get('rule_id', 'N/A')}]
================================================================================

1. QUIÉN (Identificación del Sujeto):
El sujeto del reporte es {customer.get('name', 'Desconocido')} [KYC: Name], cuenta #{customer.get('account_number', 'N/A')} [KYC: Account], ocupación: '{customer.get('occupation', 'No especificado')}' [KYC: Occupation], ingreso mensual declarado: ${customer.get('declared_monthly_income', 0):,.2f} [KYC: Income]. Calificación de riesgo: {customer.get('risk_rating', 'Medio')} [KYC: Risk].

2. QUÉ (Actividad Sospechosa):
Durante el período analizado, la cuenta registró {len(flagged_txns)} transacción(es) alertada(s) por un monto total de ${total_amount:,.2f} [Txn Records]. Regla activada: {alert.get('rule_name')} [Rule: {alert.get('rule_id', 'N/A')}].

3. CUÁNDO (Período Temporal):
La actividad sospechosa se concentró entre {date_start} y {date_end} [Txn Records].

4. DÓNDE (Jurisdicción y Canales):
Canales utilizados: {', '.join(channels)} [Txn Channels].
Contrapartes registradas: {', '.join(counterparties) if counterparties else 'Ninguna / Depósitos en Efectivo'} [Counterparty Data].

5. POR QUÉ (Fundamento de la Sospecha):
{reasons_text}
El volumen total de ${total_amount:,.2f} excede sustancialmente el perfil habitual esperado de ${customer.get('expected_monthly_volume', {}).get('deposits', 0):,.2f} [KYC: Baseline] sin justificación económica acreditada.

6. CÓMO (Metodología y Tipología):
El patrón presenta características típicas de {alert.get('archetype', 'Actividad Inusual')} ejecutado a través de {', '.join(channels[:3])}.

================================================================================
[BORRADOR GENERADO POR AML COPILOT — VALIDACIÓN HUMANA OBLIGATORIA]
"""

    elif lang == "fr":
        return f"""[BROUILLON — NÉCESSITE UNE RÉVISION PAR L'ANALYSTE AVANT DÉPÔT]
================================================================================
DÉCLARATION DE SOUPÇON (TRACFIN / STR) — NARRATIF RÉGLEMENTAIRE
Référence de l'Alerte: {alert.get('alert_id', 'N/A')} [Règle: {alert.get('rule_id', 'N/A')}]
================================================================================

1. QUI (Identification de la Personne Signalée):
Le titulaire est {customer.get('name', 'Inconnu')} [KYC: Name], compte #{customer.get('account_number', 'N/A')} [KYC: Account], profession déclarée: '{customer.get('occupation', 'Non précisé')}' [KYC: Occupation], revenu mensuel déclaré: ${customer.get('declared_monthly_income', 0):,.2f} [KYC: Income]. Niveau de risque: {customer.get('risk_rating', 'Moyen')} [KYC: Risk].

2. QUOI (Activité Suspecte):
L'activité comprend {len(flagged_txns)} transaction(s) signalée(s) pour un volume total de ${total_amount:,.2f} [Txn Records] sous la règle: {alert.get('rule_name')} [Rule: {alert.get('rule_id', 'N/A')}].

3. QUAND (Période d'Exécution):
Transactions observées entre le {date_start} et le {date_end} [Txn Records].

4. OÙ (Canaux et Juridictions):
Canaux observés: {', '.join(channels)} [Txn Channels].
Contreparties: {', '.join(counterparties) if counterparties else 'Aucune / Espèces'} [Counterparty Data].

5. POURQUOI (Motif du Soupçon):
{reasons_text}
Le montant total de ${total_amount:,.2f} excède anormalement le profil attendu de ${customer.get('expected_monthly_volume', {}).get('deposits', 0):,.2f} [KYC: Baseline].

6. COMMENT (Typologie Observée):
Le schéma correspond à une typologie de {alert.get('archetype', 'Activité Inhabituelle')} opérée via {', '.join(channels[:3])}.

================================================================================
[DOCUMENT PRÉPARÉ PAR LE COPILOTE AML — VALIDATION ANALYSTE REQUISE]
"""

    elif lang == "ar":
        return f"""[مسودة — تتطلب مراجعة المحلل المالي قبل الاعتماد والإرسال]
================================================================================
تقرير المعاملات المشبوهة (STR) — الوحدة التنظيمية لمكافحة غسل الأموال
مرجع التنبيه: {alert.get('alert_id', 'N/A')} [Rule: {alert.get('rule_id', 'N/A')}]
================================================================================

1. الهوية (معلومات العميل):
العميل المشتبه به: {customer.get('name', 'Unknown')} [KYC: Name]، الحساب رقم #{customer.get('account_number', 'N/A')} [KYC: Account]، المهنة المعلنة: '{customer.get('occupation', 'غير محدد')}' [KYC: Occupation]، الدخل الشهري المصرح به: ${customer.get('declared_monthly_income', 0):,.2f} [KYC: Income].

2. نوع النشاط (النشاط المشبوه):
تم رصد عدد {len(flagged_txns)} معاملة مشبوهة بقيمة إجمالية قدرها ${total_amount:,.2f} [Txn Records]، بموجب قاعدة المراقبة: {alert.get('rule_name')} [Rule: {alert.get('rule_id', 'N/A')}].

3. الإطار الزمني:
تمت العمليات في الفترة ما بين {date_start} و {date_end} [Txn Records].

4. قنوات التنفيذ والأطراف المقابلة:
القنوات: {', '.join(channels)} [Txn Channels].
الأطراف المستفيدة: {', '.join(counterparties) if counterparties else 'إيداعات نقدية مباشرة'} [Counterparty Data].

5. أسباب الاشتباه:
{reasons_text}
المبلغ الإجمالي البالغ ${total_amount:,.2f} يتجاوز بشكل كبير السلوك المالي المتوقع [KYC: Baseline] دون وجود مبرر اقتصادي معتمد.

================================================================================
[مسودة تم إعدادها بواسطة نظام الذكاء الاصطناعي — يلزم اعتماد المحلل البشري]
"""

    # Default: English
    return f"""[DRAFT — REQUIRES ANALYST REVIEW BEFORE SUBMISSION]
================================================================================
SUSPICIOUS TRANSACTION REPORT (STR) NARRATIVE DRAFT
Alert Reference: {alert.get('alert_id', 'N/A')} [Rule: {alert.get('rule_id', 'N/A')}]
================================================================================

1. WHO (Subject Information):
The subject of this report is {customer.get('name', 'Unknown')} [KYC: Name], account #{customer.get('account_number', 'N/A')} [KYC: Account], an individual whose declared occupation is '{customer.get('occupation', 'Unspecified')}' [KYC: Occupation] with a declared monthly income of ${customer.get('declared_monthly_income', 0):,.2f} [KYC: Income]. Account risk rating: {customer.get('risk_rating', 'Medium')} [KYC: Risk].

2. WHAT (Suspicious Activity):
During the period under review, the account exhibited unusual activity consisting of {len(flagged_txns)} flagged transaction(s) aggregating to ${total_amount:,.2f} [Txn Records]. The triggering activity is categorized under monitoring rule: {alert.get('rule_name', 'Rule')} [Rule: {alert.get('rule_id', 'N/A')}].

3. WHEN (Timeframe):
The activity occurred between {date_start} and {date_end} [Txn Records], representing a concentrated burst of transactions over an abbreviated window.

4. WHERE (Jurisdiction & Channels):
Transactions originated/settled across channels including: {', '.join(channels)} [Txn Channels].
Counterparties identified: {', '.join(counterparties) if counterparties else 'None / Cash Deposits'} [Counterparty Data].

5. WHY (Basis for Suspicion):
The activity warrants escalation due to the following specific deviations from the subject's customer profile and standard AML typologies:
{reasons_text}
The aggregated volume of ${total_amount:,.2f} significantly exceeds the subject's expected monthly volume of ${customer.get('expected_monthly_volume', {}).get('deposits', 0):,.2f} [KYC: Baseline] with no verified economic or commercial justification on file.

6. HOW (Methodology / Typology):
The pattern reflects characteristics of {alert.get('archetype', 'Suspicious Activity')}, specifically executed via {', '.join(channels[:3])}.

SUPPORTING EVIDENCE SUMMARY:
- Primary Trigger: {alert.get('trigger_summary', 'N/A')} [Rule: {alert.get('rule_id', 'N/A')}]
- Referenced Flagged Transactions: {', '.join([t.get('txn_id', '') for t in flagged_txns[:6]])} [Txn Records]

================================================================================
[DRAFT — PREPARED BY AML COPILOT. MUST BE VERIFIED AND APPROVED BY ANALYST]
"""
