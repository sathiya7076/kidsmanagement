from flask import Blueprint, render_template, request
from flask_login import login_required
from models import LearningResource

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

@learning_bp.route('/')
@login_required
def index():
    age_filter = request.args.get('age', 'all')
    type_filter = request.args.get('type', 'all')
    search = request.args.get('q', '').strip()

    query = LearningResource.query

    if age_filter and age_filter != 'all':
        query = query.filter((LearningResource.age_group == age_filter) | (LearningResource.age_group == 'all'))

    if type_filter and type_filter != 'all':
        query = query.filter_by(type=type_filter)

    if search:
        query = query.filter(
            LearningResource.title.ilike(f'%{search}%') |
            LearningResource.description.ilike(f'%{search}%') |
            LearningResource.category.ilike(f'%{search}%')
        )

    resources = query.order_by(LearningResource.title.asc()).all()

    return render_template(
        'learning/index.html',
        resources=resources,
        current_age=age_filter,
        current_type=type_filter,
        search=search
    )

@learning_bp.route('/<int:resource_id>')
@login_required
def detail(resource_id):
    resource = LearningResource.query.get_or_404(resource_id)
    related = LearningResource.query.filter(
        LearningResource.type == resource.type,
        LearningResource.id != resource.id
    ).limit(3).all()

    return render_template('learning/detail.html', resource=resource, related=related)
