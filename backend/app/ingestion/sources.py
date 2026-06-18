"""Source configurations for the multi-source web crawler.

Each source defines where to crawl (sitemap + fallback seed URLs), how to
filter URLs to article pages only, and what crawl-delay to use.
"""

from urllib.parse import urlparse


def _is_revenue_article(url: str) -> bool:
    path = urlparse(url).path
    if not path.startswith("/en/"):
        return False
    parts = [p for p in path.split("/") if p]
    if len(parts) < 3:
        return False
    exclude = (
        "/media/", "/news/", "/press-release", "/budget-overview",
        "/leaflets/", "/forms/", "/tax-practitioners/tdm/",
        "/about/", "/contact-us/", "/online-services/login",
    )
    return not any(e in path for e in exclude) and not path.endswith((".pdf", ".docx", ".zip", ".xlsx"))


def _is_govie_dsp_article(url: str) -> bool:
    # gov.ie restructured — DSP services now live at /en/department-of-social-protection/services/
    path = urlparse(url).path
    return (
        path.startswith("/en/department-of-social-protection/services/")
    ) and not path.endswith((".pdf", ".zip"))


def _is_hse_article(_url: str) -> bool:
    # HSE website is under reconstruction — skip crawling
    return False


def _is_rtb_article(url: str) -> bool:
    # rtb.ie restructured — content under /renting/, /disputes/, /register-tenancies/, /compliance/
    path = urlparse(url).path
    allowed_prefixes = ("/renting/", "/disputes/", "/register-tenancies/", "/compliance/", "/resources/", "/notice-of-termination-guides/")
    if not any(path.startswith(p) for p in allowed_prefixes):
        return False
    exclude = ("/news/", "/careers/", "/media/", "/check-the-register/", "/data-insights/", "/events/")
    return not any(e in path for e in exclude) and not path.endswith((".pdf", ".zip", ".docx"))


def _is_wrc_article(url: str) -> bool:
    # WRC guidance content lives under /en/what_you_should_know/ and /en/complaints_disputes/
    # Exclude /archive/, /cases/ (old tribunal decisions), and utility pages
    path = urlparse(url).path
    allowed_prefixes = ("/en/what_you_should_know/", "/en/complaints_disputes/")
    if not any(path.startswith(p) for p in allowed_prefixes):
        return False
    exclude = ("/en/archive/", "/en/cases/", "/en/news", "/en/contact", "/en/search")
    return not any(e in path for e in exclude) and not path.endswith((".pdf", ".zip", ".docx"))


# ---------------------------------------------------------------------------
# Source registry — add new sources here
# ---------------------------------------------------------------------------

SOURCES: dict[str, dict] = {
    "citizensinformation": {
        "source": "citizensinformation",
        "sitemap_url": "https://www.citizensinformation.ie/sitemap.xml",
        "seed_urls": [
            "https://www.citizensinformation.ie/en/moving-country/moving-to-ireland/rights-of-residence-in-ireland/residence-rights-eu-national/",
            "https://www.citizensinformation.ie/en/moving-country/working-in-ireland/employment-permits/critical-skills-employment-permit/",
            "https://www.citizensinformation.ie/en/money-and-tax/tax/income-tax/how-your-tax-is-calculated/",
            "https://www.citizensinformation.ie/en/social-welfare/unemployed-people/jobseekers-benefit/",
            "https://www.citizensinformation.ie/en/health/medical-cards-and-gp-visit-cards/medical-card/",
        ],
        "allowed_domain": "citizensinformation.ie",
        "url_filter": lambda url: (
            urlparse(url).path.startswith("/en/") and
            len([p for p in urlparse(url).path.split("/") if p]) >= 3 and
            not urlparse(url).path.endswith((".pdf", ".docx", ".zip"))
        ),
        "crawl_delay": 1.2,
        "default_max_pages": 500,
    },

    "revenue": {
        "source": "revenue",
        "sitemap_url": "https://www.revenue.ie/sitemap.xml",
        "seed_urls": [
            # PAYE & payroll
            "https://www.revenue.ie/en/jobs-and-pensions/paye-and-payroll/what-is-paye.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/emergency-tax/index.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/end-of-year-process/employment-detail-summary.aspx",
            # USC
            "https://www.revenue.ie/en/jobs-and-pensions/usc/index.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/usc/usc-exemptions.aspx",
            # Tax credits & reliefs
            "https://www.revenue.ie/en/income-tax-credits-and-reliefs/credits/index.aspx",
            "https://www.revenue.ie/en/income-tax-credits-and-reliefs/credits/personal-circumstances/home-carer-tax-credit.aspx",
            "https://www.revenue.ie/en/income-tax-credits-and-reliefs/credits/personal-circumstances/single-person-child-carer-credit.aspx",
            "https://www.revenue.ie/en/income-tax-credits-and-reliefs/reliefs/education/third-level-fees.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/tax-relief-for-expenses/health-expenses/index.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/tax-relief-for-expenses/flat-rate-expenses.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/tax-relief-for-expenses/remote-working-expenses/index.aspx",
            "https://www.revenue.ie/en/jobs-and-pensions/tax-relief-for-expenses/pension-contributions.aspx",
            # Rent & property
            "https://www.revenue.ie/en/property/local-property-tax/index.aspx",
            "https://www.revenue.ie/en/property/local-property-tax/paying-lpt/index.aspx",
            "https://www.revenue.ie/en/property/local-property-tax/exemptions-and-reliefs/index.aspx",
            "https://www.revenue.ie/en/property/rental-income/index.aspx",
            "https://www.revenue.ie/en/property/rental-income/what-expenses-can-be-deducted.aspx",
            # CGT & CAT
            "https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-assets/capital-gains-tax.aspx",
            "https://www.revenue.ie/en/gains-gifts-and-inheritance/cat-index.aspx",
            # VAT
            "https://www.revenue.ie/en/vat/index.aspx",
            "https://www.revenue.ie/en/vat/vat-registration/index.aspx",
            "https://www.revenue.ie/en/vat/vat-rates/index.aspx",
            # Self-assessment
            "https://www.revenue.ie/en/self-assessment-and-self-employment/filing-your-tax-return/who-must-file-a-return.aspx",
            "https://www.revenue.ie/en/self-assessment-and-self-employment/preliminary-tax/index.aspx",
            # myAccount & ROS
            "https://www.revenue.ie/en/online-services/services/manage-your-record/myaccount.aspx",
            "https://www.revenue.ie/en/online-services/ros/index.aspx",
            # Cryptocurrency
            "https://www.revenue.ie/en/gains-gifts-and-inheritance/crypto-assets/index.aspx",
        ],
        "allowed_domain": "revenue.ie",
        "url_filter": _is_revenue_article,
        "crawl_delay": 1.5,
        "default_max_pages": 150,
    },

    "dsp": {
        "source": "dsp",
        "sitemap_url": None,  # gov.ie sitemaps contain publication noise — use verified seed URLs
        "seed_urls": [
            # Unemployment
            "https://www.gov.ie/en/department-of-social-protection/services/jobseekers-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/jobseekers-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/back-to-work-enterprise-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/community-employment-programme/",
            "https://www.gov.ie/en/department-of-social-protection/services/benefit-payment-for-65-year-olds/",
            # Families & children
            "https://www.gov.ie/en/department-of-social-protection/services/working-family-payment-wfp/",
            "https://www.gov.ie/en/department-of-social-protection/services/child-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/one-parent-family-payment/",
            "https://www.gov.ie/en/department-of-social-protection/services/back-to-school-clothing-and-footwear-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/guardians-payment/",
            # Maternity, parental, adoption
            "https://www.gov.ie/en/department-of-social-protection/services/maternity-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/paternity-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/parents-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/adoptive-benefit/",
            # Illness & disability
            "https://www.gov.ie/en/department-of-social-protection/services/disability-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/invalidity-pension/",
            "https://www.gov.ie/en/department-of-social-protection/services/partial-capacity-benefit/",
            "https://www.gov.ie/en/department-of-social-protection/services/blind-pension/",
            # Carers
            "https://www.gov.ie/en/department-of-social-protection/services/carers-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/carers-benefit/",
            # Pensions
            "https://www.gov.ie/en/department-of-social-protection/services/state-pension-contributory/",
            "https://www.gov.ie/en/department-of-social-protection/services/state-pension-non-contributory/",
            # Education & work activation
            "https://www.gov.ie/en/department-of-social-protection/services/back-to-education-allowance/",
            # Housing & living costs
            "https://www.gov.ie/en/department-of-social-protection/services/basic-supplementary-welfare-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/household-benefits-package/",
            "https://www.gov.ie/en/department-of-social-protection/services/fuel-allowance/",
            "https://www.gov.ie/en/department-of-social-protection/services/bereaved-parent-grant/",
        ],
        "allowed_domain": "gov.ie",
        "url_filter": _is_govie_dsp_article,
        "crawl_delay": 2.0,
        "default_max_pages": 60,
    },

    "hse": {
        "source": "hse",
        "sitemap_url": None,
        # HSE website is under reconstruction (hse.ie redirects to /website-update/).
        # Live crawling is disabled. Fixture data in fixtures/hse.json is used instead.
        "seed_urls": [],
        "allowed_domain": "hse.ie",
        "url_filter": _is_hse_article,
        "crawl_delay": 1.5,
        "default_max_pages": 0,
    },

    "rtb": {
        "source": "rtb",
        "sitemap_url": None,  # rtb.ie/sitemap.xml redirects to /about/ — use seed URLs
        "seed_urls": [
            # Tenant & landlord rights
            "https://rtb.ie/renting/",
            "https://rtb.ie/renting/rights-responsibilities/",
            "https://rtb.ie/renting/rights-responsibilities/tenant-rights-responsibilities/",
            "https://rtb.ie/renting/rights-responsibilities/landlord-rights-responsibilities/",
            "https://rtb.ie/renting/rights-responsibilities/security-deposits/",
            "https://rtb.ie/renting/rights-responsibilities/minimum-standards-for-rental-properties/",
            "https://rtb.ie/renting/rights-responsibilities/wear-and-tear/",
            # Tenancy types
            "https://rtb.ie/renting/types-of-tenancies/",
            "https://rtb.ie/renting/types-of-tenancies/private-residential-tenancies/",
            "https://rtb.ie/renting/types-of-tenancies/cost-rental-housing/",
            "https://rtb.ie/renting/types-of-tenancies/student-specific-accommodation/",
            "https://rtb.ie/renting/tenants-right-to-stay-in-a-rented-property/",
            # Beginning & ending a tenancy
            "https://rtb.ie/renting/beginning-a-tenancy/",
            "https://rtb.ie/renting/beginning-a-tenancy/tenant-checklist/",
            "https://rtb.ie/renting/beginning-a-tenancy/landlord-checklist/",
            "https://rtb.ie/renting/ending-a-tenancy/",
            "https://rtb.ie/renting/ending-a-tenancy/how-a-tenant-can-end-a-tenancy/",
            "https://rtb.ie/renting/how-a-landlord-can-end-a-tenancy/",
            "https://rtb.ie/notice-of-termination-guides/",
            # Rent setting & RPZ
            "https://rtb.ie/renting/setting-reviewing-rent/",
            "https://rtb.ie/renting/guide-to-rent-review-notices/",
            "https://rtb.ie/renting/guide-to-rent-setting-notices/",
            "https://rtb.ie/renting/rental-law-changes-from-1-march/",
            # Disputes
            "https://rtb.ie/disputes/",
            "https://rtb.ie/disputes/disputes-process/",
            # Registration
            "https://rtb.ie/register-tenancies/",
        ],
        "allowed_domain": "rtb.ie",
        "url_filter": _is_rtb_article,
        "crawl_delay": 1.5,
        "default_max_pages": 50,
    },

    "wrc": {
        "source": "wrc",
        "sitemap_url": None,  # WRC sitemap returns 404; use seed URLs
        "seed_urls": [
            # Pay & hours
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/national minimum wage/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/working_hours/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/payslips/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/deductions from pay/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/sunday premium entitlement/",
            "https://www.workplacerelations.ie/en/what_you_should_know/hours-and-wages/tips-and-gratuities/",
            # Leave
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/annual-leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/sick-leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/maternity leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/paternity leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/parental leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/parent-s-leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/carer's leave/",
            "https://www.workplacerelations.ie/en/what_you_should_know/leave/domestic-violence-leave/",
            # Ending employment
            "https://www.workplacerelations.ie/en/what_you_should_know/ending the employment relationship/",
            "https://www.workplacerelations.ie/en/what_you_should_know/ending the employment relationship/redundancy/",
            "https://www.workplacerelations.ie/en/what_you_should_know/ending the employment relationship/dismissal/",
            "https://www.workplacerelations.ie/en/what_you_should_know/ending the employment relationship/minimum notice/",
            "https://www.workplacerelations.ie/en/what_you_should_know/ending the employment relationship/collective redundancies/",
            # Employment types
            "https://www.workplacerelations.ie/en/what_you_should_know/employment_types/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employment_types/part-time-workers/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employment_types/agency-workers/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employment_types/zero-hours-working-practices/",
            # Employer obligations
            "https://www.workplacerelations.ie/en/what_you_should_know/employer-obligations/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employer-obligations/terms-of-employment/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employer-obligations/protection-of-whistleblowers/",
            "https://www.workplacerelations.ie/en/what_you_should_know/employer-obligations/auto-enrolment-scheme/",
            # Equality
            "https://www.workplacerelations.ie/en/what_you_should_know/equal-status-and-employment-equality/",
            # Public holidays
            "https://www.workplacerelations.ie/en/what_you_should_know/public-holidays/",
            # Disputes
            "https://www.workplacerelations.ie/en/complaints_disputes/",
            "https://www.workplacerelations.ie/en/complaints_disputes/making_a_complaint/",
            "https://www.workplacerelations.ie/en/complaints_disputes/mediation/",
            "https://www.workplacerelations.ie/en/complaints_disputes/adjudication/",
        ],
        "allowed_domain": "workplacerelations.ie",
        "url_filter": _is_wrc_article,
        "crawl_delay": 1.5,
        "default_max_pages": 60,
    },
}
