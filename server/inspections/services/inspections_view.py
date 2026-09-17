from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta

# Models Import
InspectionCategoryModel = apps.get_model(
    "inspections", "InspectionCategoryModel")
InspectionModel = apps.get_model(
    "inspections", "InspectionModel")
InspectionQuestionModel = apps.get_model(
    "inspections", "InspectionQuestionModel")
InspectionResponseModel = apps.get_model(
    "inspections", "InspectionResponseModel")
IssueModel = apps.get_model(
    "issues", "IssueModel")
ActivityModel = apps.get_model(
    "projects", "ActivityModel")

# PENDING INSPECTION STATUS


# Delete
def get_pending_inspection_data(
        project
):
    inspection_status = 'Not Started'
    inspection_btn = 'Start Inspection'
    inspection_insight = 'Daily inspection is still pending. Start todays inspection to keep the project on track.'
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project)

    inspections_questions_count = inspection_questions.count()

    return {
        # INSPECTIONS
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_insight": inspection_insight,
        "inspections_questions_count": inspections_questions_count,
    }


# GET STARTED INSPECTION
def get_inspection_data(
        inspection,
        current_user=None,
):
    today = timezone.now()
    project = inspection.project

    # ==================================================
    # START DAILY INSPECTION
    # ==================================================
    if inspection.status == "pending":
        inspection.status = "in_progress"
        inspection.started_at = today
        inspection.started_by = current_user
        inspection.save(
            update_fields=[
                "status",
                "started_at",
                "started_by",
            ]
        )

        # Get All Project Questions
        inspection_questions = InspectionQuestionModel.objects.filter((
            Q(is_default=True) &
            Q(project_question__isnull=True)
        ) |
            (
            Q(is_default=False) &
            Q(project_question=project)
        )).exclude(not_applicable=project).order_by(
            "category__order",
            "order",
        )

        # Create All Responses for All Questions
        InspectionResponseModel.objects.bulk_create([
            InspectionResponseModel(
                inspection=inspection,
                question=question,
            )
            for question in inspection_questions
        ])

    # ==================================================
    # GET UPDATED INSPECTION DATA
    # ==================================================
    checklist = (
        InspectionResponseModel.objects
        .filter(
            inspection=inspection
        )
        .select_related(
            "question",
            "question__category",
        )
        .order_by(
            "question__category__order",
            "question__order",
        )
    )

   # Group responses by category
    grouped_checklist = defaultdict(list)

    for response in checklist:
        category = response.question.category
        grouped_checklist[category].append(response)

    # Convert into template-friendly structure
    grouped_checklist = [
        {
            "category": category,
            "name": category.name,
            "responses": responses,

            # Statistics
            "tot_question": len(responses),

            "an_questions": sum(
                1 for response in responses
                if response.answer is not None
            ),

            "failed_questions": sum(
                1
                for response in responses
                if response.answer == "fail"
            ),

            # Status
            "status": (
                "missing"
                if sum(1 for response in responses if response.answer is not None) == 0
                else "complete"
                if sum(1 for response in responses if response.answer is not None) == len(responses)
                else "incomplete"
            ),
        }
        for category, responses in grouped_checklist.items()
    ]

    # INSPECTION STATUS UPDATE
    if inspection.status == 'in_progress':
        inspection_status = 'In Progress'
        inspection_btn = 'Continue Inspection'
        inspection_insight = 'Todays inspection has started but no questions have been answered yet.'
    elif inspection.status == 'draft':
        inspection_status = 'Draft'
        inspection_btn = 'Continue Inspection'
        inspection_insight = 'Todays inspection has been saved as draft'
    else:
        inspection_status = 'In Progress'
        inspection_btn = 'Continue Inspection'
        inspection_insight = 'Todays inspection has started but no questions have been answered yet.'

    return {
        "grouped_checklist": grouped_checklist,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_insight": inspection_insight,
    }


# PROJECT DETAILS PAGE
def get_project_daily_inspection(
    project,
    current_user=None,
):
    today = timezone.now()
    current_project = project

    # ==================================================
    # GET OR CREATE PROJECT DAILY INSPECTION
    # ==================================================

    inspection = InspectionModel.objects.filter(
        Q(created_at__date=today) & Q(project=project)
    ).first()

    grouped_checklist = None

    # GET THE PROJECT TODAYS INSPECTION
    if inspection:
        todays_inspection = inspection
        if todays_inspection.status == 'pending':
            pending_inspection = get_pending_inspection_data(project=project)
            inspection_status = pending_inspection['inspection_status']
            inspection_btn = pending_inspection['inspection_btn']
            inspection_insight = pending_inspection['inspection_insight']
            inspections_questions_count = pending_inspection['inspections_questions_count']
        else:
            current_inspection = get_inspection_data(
                inspection=inspection, current_user=current_user)
            inspection_status = current_inspection['inspection_status']
            inspection_btn = current_inspection['inspection_btn']
            inspection_insight = current_inspection['inspection_insight']
            inspections_questions_count = 0
            grouped_checklist = current_inspection['grouped_checklist']
    else:
        # NO DAILY INSPECTION CREATED
        pending_inspection = get_pending_inspection_data(project=project)
        inspection_status = pending_inspection['inspection_status']
        inspection_btn = pending_inspection['inspection_btn']
        inspection_insight = pending_inspection['inspection_insight']
        inspections_questions_count = pending_inspection['inspections_questions_count']
        # CREATE PROJECT INSPECTION MODEL OBJECT
        todays_inspection = InspectionModel.objects.create(
            project=project,
            inspection_date=today,
        )

    return {
        # INSPECTIONS
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_insight": inspection_insight,
        "inspections_questions_count": inspections_questions_count,
        "todays_inspection": todays_inspection,
        "grouped_checklist": grouped_checklist,
    }


# ======================================================================================


# PROJECT DETAILS FUNCTION DATA ********* USE
def get_project_details_inspection_data(
        inspection,
):

    unanswered_count = 0
    answered_count = 0
    failed_count = 0
    items_count = 0

    checklist = (
        InspectionResponseModel.objects
        .filter(
            inspection=inspection
        )
        .select_related(
            "question",
            "question__category",
        )
        .order_by(
            "question__category__order",
            "question__order",
        )
    )

    # Group responses by category
    grouped_checklist = defaultdict(list)

    for response in checklist:
        category = response.question.category
        grouped_checklist[category].append(response)

    # Convert into template-friendly structure
    grouped_checklist = [
        {
            "category": category,
            "name": category.name,
            "responses": responses,

            # Statistics
            "tot_question": len(responses),

            "an_questions": sum(
                1 for response in responses
                if response.answer is not None
            ),

            "failed_questions": sum(
                1
                for response in responses
                if response.answer == "fail"
            ),

            # Status
            "status": (
                "Pending"
                if sum(1 for response in responses if response.answer is not None) == 0
                else "Complete"
                if sum(1 for response in responses if response.answer is not None) == len(responses)
                else "Incomplete"
            ),
        }
        for category, responses in grouped_checklist.items()
    ]

    # CHECK COUNTS
    for item in checklist:
        items_count += 1
        if item.answer == None:
            unanswered_count += 1
        elif item.answer == 'fail':
            failed_count += 1
            answered_count += 1
        else:
            answered_count += 1

    # DAILY INSPECTIONS INSIGHTS
    if unanswered_count > 0:
        inspection_icon = '🟡'
        inspection_insight = f'Daily inspection is incomplete'
        inspection_action = 'Continue inspection'
        inspection_btn = 'Continue inspection'
        inspection_status = 'Incomplete'
        failed_inspections = ''
    elif answered_count == items_count and inspection.status == "in_progress":
        inspection_icon = "🟠"
        inspection_insight = "Daily inspection is ready to save."
        inspection_action = "Save inspection"
        inspection_btn = 'Save inspection'
        inspection_status = 'Ready to Save'
        failed_inspections = ''
    else:
        inspection_icon = "🟢"
        inspection_insight = "Daily inspection complete ✅"
        inspection_action = "View inspection"
        inspection_btn = 'View inspection'
        inspection_status = 'Complete'
        failed_inspections = f'({failed_count} failed items)'

    inspection_percentage = int(
        (answered_count / items_count) * 100)

    return {
        "grouped_checklist": grouped_checklist,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_insight": inspection_insight,
        "inspection_icon": inspection_icon,
        "inspection_action": inspection_action,
        "failed_inspections": failed_inspections,
        "unanswered_count": unanswered_count,
        "answered_count": answered_count,
        "total_checklists": items_count,
        "questions_count": 0,
        "inspection_percentage": inspection_percentage,
    }


def get_missed_inspection_days(project):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    current_date = project.start_date
    missed_days = []

    while current_date <= yesterday:

        # Only count Monday-Friday
        if current_date.weekday() < 5:

            inspection_exists = InspectionModel.objects.filter(
                project=project,
                inspection_date=current_date,
                status="complete",
            ).exists()

            if not inspection_exists:
                missed_days.append(current_date)

        current_date += timedelta(days=1)

    return missed_days


# PROJECT DETAILS DAILY INSPECTION DETAILS
def get_project_details_daily_inspection(
        project,
        current_user=None,
):
    today = timezone.now()
    inspection = InspectionModel.objects.filter(
        Q(created_at__date=today) & Q(project=project)
    ).first()

    # ==================================================
    # NO DAILY INSPECTION CREATED DATA
    # ==================================================

    # Get All Project Questions
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project).order_by(
        "category__order",
        "order",
    )

    if inspection == None:
        inspection_status = 'Not Started'
        inspection_btn = 'Start Inspection'
        inspection_icon = '🔴'
        inspection_insight = 'Daily inspection not started'
        inspection_action = 'Start inspection'
        failed_inspections = ''
        questions_count = inspection_questions.count()
        checklist_items = None
        unanswered_count = 1
        inspection_percentage = 0
        answered_count = 0
        total_checklists = 0

    # ==================================================
    # GET CREATED INSPECTION DATA
    # ==================================================
    else:
        todays_inspection_data = get_project_details_inspection_data(
            inspection=inspection)
        inspection_icon = todays_inspection_data['inspection_icon']
        inspection_status = todays_inspection_data['inspection_status']
        inspection_btn = todays_inspection_data['inspection_btn']
        inspection_insight = todays_inspection_data['inspection_insight']
        failed_inspections = todays_inspection_data['failed_inspections']
        inspection_action = todays_inspection_data['inspection_action']
        questions_count = todays_inspection_data['questions_count']
        checklist_items = todays_inspection_data['grouped_checklist']
        unanswered_count = todays_inspection_data['unanswered_count']
        inspection_percentage = todays_inspection_data['inspection_percentage']
        answered_count = todays_inspection_data['answered_count']
        total_checklists = todays_inspection_data['total_checklists']

    # ==================================================
    # CHECK MISSED INSPECTIONS
    # ==================================================
    missed_inspection_days = get_missed_inspection_days(project)
    missed_inspection_count = len(missed_inspection_days)
    if missed_inspection_count > 0:
        missed_inspection_icon = '🔴'
        if missed_inspection_count > 1:
            missed_inspections_text = f'{missed_inspection_count} daily inspections were missed'
        else:
            missed_inspections_text = f'{missed_inspection_count} daily inspection missed'
    else:
        missed_inspection_icon = ''
        missed_inspections_text = ''

    return {
        # INSPECTIONS
        "missed_inspection_days": missed_inspection_days,
        "missed_inspections_text": missed_inspections_text,
        "missed_inspection_count": missed_inspection_count,
        "missed_inspection_icon": missed_inspection_icon,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_icon": inspection_icon,
        "inspection_insight": inspection_insight,
        "failed_inspections": failed_inspections,
        "inspection_action": inspection_action,
        "questions_count": questions_count,
        "checklist_items": checklist_items,
        "unanswered_count": unanswered_count,
        "inspection_percentage": inspection_percentage,
        "answered_count": answered_count,
        "total_checklists": total_checklists,
    }


# DAILY INSPECTION CHECKLIST ITEMS PAGE
def get_project_daily_inspection_new(
    current_user=None,
    project=None,
):

    today = timezone.now()
    inspections_data = []
    total_answered_count = 0
    total_questions_count = 0
    total_unanswered_count = 0

    inspection = InspectionModel.objects.filter(
        Q(created_at__date=today) & Q(project=project)
    ).first()

    # ==================================================
    # CHECK IF INSPECTION CREATED IF NOT CREATE ONE
    # ==================================================
    if inspection == None:
        inspection = InspectionModel.objects.create(
            project=project,
            status="in_progress",
            started_at=today,
            started_by=current_user,
        )

        # Get All Project Questions
        inspection_questions = InspectionQuestionModel.objects.filter((
            Q(is_default=True) &
            Q(project_question__isnull=True)
        ) |
            (
            Q(is_default=False) &
            Q(project_question=project)
        )).exclude(not_applicable=project).order_by(
            "category__order",
            "order",
        )

        # Create All Responses for All Questions
        InspectionResponseModel.objects.bulk_create([
            InspectionResponseModel(
                inspection=inspection,
                question=question,
            )
            for question in inspection_questions
        ])

        # =============== CREATE PROJECT TIMELINE ===============
        company = current_user.company
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Inspection Started',
            description=f'{current_user.first_name} {current_user.last_name} started daily inspection',
            icon_type='inspection',
        )

    # ==================================================
    # GET INSPECTION CHECKLIST ITEMS
    # ==================================================
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project).order_by(
        "category__order",
        "order",
    )

    inspection_categories = InspectionCategoryModel.objects.filter(
        (
            Q(is_default=True) &
            Q(project__isnull=True)
        ) |
        (
            Q(is_default=False) &
            Q(project=project)
        )
    ).exclude(not_applicable=project)

    for category in inspection_categories:
        responses = InspectionResponseModel.objects.filter(
            question__category=category,
            inspection=inspection,
        ).prefetch_related(
            "inspection_response",
        )

        total_questions = responses.count()
        total_answered = responses.filter(
            answer__isnull=False
        ).exclude(
            answer=""
        ).count()

        total_unanswered = responses.filter(answer=None)
        total_unanswered_count += total_unanswered.count()

        failed_items = responses.filter(answer="fail").count()

        total_answered_count += total_answered
        total_questions_count += total_questions

        inspections_data.append({
            "category": category,
            "responses": responses,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "failed_items": failed_items,
        })

    inspection_percentage = int(
        (total_answered_count / total_questions_count) * 100)

    # DAILY INSPECTIONS STATUS
    if total_unanswered_count > 0:
        inspection_icon = '🟡'
        inspection_status = 'Incomplete'
    elif total_answered_count == total_questions_count and inspection.status == "in_progress":
        inspection_icon = "🟠"
        inspection_status = 'Ready to Save'
    else:
        inspection_icon = "🟢"
        inspection_status = 'Complete'

    return {
        "inspection": inspection,
        "categories": inspections_data,
        "total_questions_count": total_questions_count,
        "total_answered_count": total_answered_count,
        "inspection_percentage": inspection_percentage,
        "inspection_status": inspection_status,
    }
