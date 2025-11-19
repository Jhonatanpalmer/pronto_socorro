"""Lookup helpers for CID-10 (ICD-10) descriptions used in RH workflows.

This module keeps a lightweight, extensible mapping of CID-10 codes to their
respective descriptions. The mapping is intentionally small and can be expanded
as needed by editing the ``CID10_DESCRIPTIONS`` dictionary or replacing the
loading strategy with a call to an external dataset.
"""

from __future__ import annotations

CID10_DESCRIPTIONS = {
    # Capítulo I – Algumas doenças infecciosas e parasitárias
    "A00": "Cólera",
    "A01": "Febre tifoide e paratifoide",
    "A09": "Diarreia e gastroenterite de origem infecciosa presumível",
    "B20": "Doença pelo vírus da imunodeficiência humana [HIV] resultando em doenças infecciosas e parasitárias",
    "B34": "Infecções virais de localizações não especificadas",
    # Capítulo II – Neoplasias
    "C34": "Neoplasia maligna dos brônquios e do pulmão",
    "C50": "Neoplasia maligna da mama",
    # Capítulo III – Doenças do sangue e dos órgãos hematopoéticos
    "D50": "Anemia por deficiência de ferro",
    "D64": "Outras anemias",
    # Capítulo IV – Doenças endócrinas, nutricionais e metabólicas
    "E10": "Diabetes mellitus insulino-dependente",
    "E11": "Diabetes mellitus não insulino-dependente",
    "E66": "Obesidade",
    # Capítulo V – Transtornos mentais e comportamentais
    "F20": "Esquizofrenia",
    "F21": "Transtorno esquizotípico",
    "F25": "Transtornos esquizoafetivos",
    "F32": "Episódios depressivos",
    "F33": "Transtorno depressivo recorrente",
    "F41": "Outros transtornos de ansiedade",
    "F43": "Reações ao estresse grave e transtornos de adaptação",
    "F84": "Transtornos globais do desenvolvimento",
    # Capítulo VI – Doenças do sistema nervoso
    "G40": "Epilepsia",
    "G43": "Enxaqueca",
    # Capítulo VII – Doenças do olho e anexos
    "H10": "Conjuntivite",
    # Capítulo IX – Doenças do aparelho circulatório
    "I10": "Hipertensão essencial (primária)",
    "I11": "Doença cardíaca hipertensiva",
    "I20": "Angina pectoris",
    "I21": "Infarto agudo do miocárdio",
    "I50": "Insuficiência cardíaca",
    "I63": "Infarto cerebral",
    # Capítulo X – Doenças do aparelho respiratório
    "J06": "Infecções agudas das vias aéreas superiores", 
    "J10": "Influenza [gripe] devido a vírus identificado",
    "J18": "Pneumonia por microrganismo não especificado",
    # Capítulo XI – Doenças do aparelho digestivo
    "K35": "Apendicite aguda",
    "K52": "Outras gastroenterites e colites não infecciosas",
    "K80": "Colelitíase",
    # Capítulo XII – Doenças da pele e do tecido subcutâneo
    "L20": "Dermatite atópica",
    # Capítulo XIII – Doenças do sistema osteomuscular e do tecido conjuntivo
    "M54": "Dorsalgia",
    "M79": "Outros transtornos dos tecidos moles",
    # Capítulo XIV – Doenças do aparelho geniturinário
    "N18": "Doença renal crônica",
    "N39": "Outros transtornos do trato urinário",
    # Capítulo XV – Gravidez, parto e puerpério
    "O80": "Parto único espontâneo",
    # Capítulo XVI – Algumas afecções originadas no período perinatal
    "P07": "Transtornos relacionados à duração da gestação e ao crescimento fetal",
    # Capítulo XVII – Malformações congênitas, deformidades e anomalias cromossômicas
    "Q21": "Malformações congênitas das câmaras cardíacas e das conexões cardio-vasculares",
    # Capítulo XVIII – Sintomas, sinais e achados anormais de exames clínicos e de laboratório
    "R07": "Dor na garganta e no peito",
    "R10": "Dor abdominal e pélvica",
    "R51": "Cefaleia",
    # Capítulo XIX – Lesões, envenenamentos e algumas outras consequências de causas externas
    "S06": "Traumatismo intracraniano",
    "T81": "Complicações de procedimentos não classificadas em outra parte",
    # Capítulo XX – Causas externas de morbidade e de mortalidade
    "V89": "Acidente de transporte não especificado",
    "W19": "Queda em mesmo nível, não especificada",
    "X59": "Exposição a causas externas não especificadas",
    "Y84": "Complicações de cuidados médicos e cirúrgicos",
    # Capítulo XXI – Fatores que influenciam o estado de saúde e o contato com os serviços de saúde
    "Z00": "Exame geral e investigação de pessoas sem queixas ou diagnóstico relatado",
    "Z76": "Pessoas em contato com os serviços de saúde por outras circunstâncias",
}


def get_cid_description(code: str | None) -> str | None:
    """Return the description for a CID-10 code if available.

    Normalizes the code by removing whitespace, converting to uppercase and
    allowing lookups either in the exact form (e.g. ``F21``) or by stripping
    subcategory separators (``F21.1`` -> ``F21``).
    """

    if not code:
        return None

    normalized = str(code).strip().upper().replace(" ", "")
    if not normalized:
        return None

    # Direct match (including subcategory with dot)
    description = CID10_DESCRIPTIONS.get(normalized)
    if description is not None:
        return description

    # Try to match without dot/subcategory portion (e.g., F21.3 -> F21)
    root = normalized.split('.')[0]
    if root and root in CID10_DESCRIPTIONS:
        return CID10_DESCRIPTIONS[root]

    return None