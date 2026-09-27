from geo_search_api.apps.ideas.models import IdeaStatuses

IDEA_STATUSES_WORKFLOW = {
    IdeaStatuses.UNDER_REVIEW: [IdeaStatuses.ACTIVE, IdeaStatuses.REJECTED],
    IdeaStatuses.REJECTED: [IdeaStatuses.UNDER_REVIEW],
    IdeaStatuses.ACTIVE: [IdeaStatuses.CLOSED],
    IdeaStatuses.CLOSED: [IdeaStatuses.ACTIVE, IdeaStatuses.INNOVATIVE],
    IdeaStatuses.INNOVATIVE: [IdeaStatuses.CLOSED],
}


def get_possible_idea_statuses(current_status):
    """
    Chose and return possible statuses according to workflow
    """
    return IDEA_STATUSES_WORKFLOW[current_status]
