from flask import render_template
from . import main_bp

ARTISTS = [
    {
        'name': 'Nova Raines',
        'emoji': '🎤',
        'genre': 'R&B · Soul',
        'service': 'Promotion',
        'metric': '+340% streams',
        'metric_color': 'purple',
        'story': 'Nova came to us as an unsigned indie artist with raw talent and zero online presence. Within 3 months of our daily promotion package, her Spotify streams increased by 340%. We ran targeted social campaigns, pitched her to 40+ playlists, and built a loyal fanbase from scratch.',
    },
    {
        'name': 'DJ Kaleo',
        'emoji': '🎧',
        'genre': 'Electronic · House',
        'service': 'Production',
        'metric': 'Signed to label',
        'metric_color': 'blue',
        'story': 'Kaleo had the beats but needed professional polish. Our production team worked with him for 6 weeks — studio sessions, mixing, mastering, and artist development. The resulting EP caught the attention of a major label A&R, leading to a full recording deal.',
    },
    {
        'name': 'Zara Vex',
        'emoji': '🎸',
        'genre': 'Alt-Rock · Indie',
        'service': 'Promotion',
        'metric': '50K followers',
        'metric_color': 'purple',
        'story': "Zara's alternative sound needed the right audience. We crafted a 90-day promotion strategy combining Instagram Reels campaigns, press outreach to music blogs, and Spotify editorial pitching. She gained 50K engaged Instagram followers and landed features in three music publications.",
    },
    {
        'name': 'Marcus Cole',
        'emoji': '🎙️',
        'genre': 'Hip-Hop',
        'service': 'Lessons + Production',
        'metric': 'Debut album',
        'metric_color': 'purple',
        'story': "Marcus enrolled in our music production lessons and simultaneously worked with our production team. In 8 months, he went from learning DAW basics to releasing a fully-produced 10-track debut album that charted on regional hip-hop charts.",
    },
    {
        'name': 'Lia Frost',
        'emoji': '🌟',
        'genre': 'Pop',
        'service': 'Promotion',
        'metric': '2M TikTok views',
        'metric_color': 'blue',
        'story': "Lia had one great single but no visibility. We identified the TikTok trend angle, crafted the campaign, coordinated with 12 content creators, and ran paid micro-targeting. One video went viral with 2M views, pushing the single into the Spotify Viral 50 chart.",
    },
]

@main_bp.route('/')
def index():
    featured = ARTISTS[:3]
    return render_template('index.html', featured_artists=featured)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/artists')
def artists():
    return render_template('artists.html', artists=ARTISTS)

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/refund')
def refund():
    return render_template('refund.html')
