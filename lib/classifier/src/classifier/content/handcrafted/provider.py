"""
Handcrafted Content Provider

This module contains battle-tested, manually curated content for the classifier.
It serves as the PRIMARY content source - the gold standard.

Structure:
- CATEGORIES: Category definitions with descriptions
- ELEMENTS: Element definitions by category
- STAGE1_EXAMPLES: Proven examples for category detection
- STAGE1_RULES: Disambiguation rules for category detection
- STAGE2_EXAMPLES: Proven examples for element extraction (by category)
- STAGE2_RULES: Rules for element extraction

To Modify:
- Edit the dictionaries/lists in this file directly
- All changes take effect immediately (no reloading needed)
- Test changes by running the pipeline on known inputs

Philosophy:
- Handcrafted content is precious - it represents human expertise
- Only add to handcrafted when you're confident the example is correct
- Use generated content for bootstrapping, then graduate to handcrafted
"""

from typing import Any, Dict, List, Optional

from ..interfaces import (
    AttributeContent,
    CategoryContent,
    ContentProvider,
    ElementContent,
    Example,
    Rule,
)

# =============================================================================
# CATEGORY DEFINITIONS
# =============================================================================

CATEGORIES: Dict[str, Dict[str, Any]] = {
    "Attendee Engagement & Interaction": {
        "description": "Feedback about connecting with others, community building, and social aspects",
        "condensed": "Connecting with others, community building, and social aspects",
        "keywords": [
            "community",
            "networking",
            "social",
            "connect",
            "peers",
            "knowledge exchange",
        ],
        "elements": [
            "Community",
            "Knowledge Exchange",
            "Networking",
            "Social Events",
        ],
    },
    "Event Logistics & Infrastructure": {
        "description": "Feedback about physical/technical infrastructure and venue-related services",
        "condensed": "Physical/technical infrastructure and venue-related services",
        "keywords": ["venue", "wifi", "food", "hotel", "transportation", "app", "technology"],
        "elements": [
            "Conference Application/Software",
            "Conference Venue",
            "Food/Beverages",
            "Hotel",
            "Technological Tools",
            "Transportation",
            "Wi-Fi",
        ],
    },
    "Event Operations & Management": {
        "description": "Feedback about how the conference was organized and run",
        "condensed": "Conference organization and management",
        "keywords": [
            "organization",
            "registration",
            "schedule",
            "timing",
            "communication",
            "management",
        ],
        "elements": [
            "Conference",
            "Conference Registration",
            "Conference Scheduling",
            "Messaging & Awareness",
        ],
    },
    "Learning & Content Delivery": {
        "description": "Feedback about educational content and how it was delivered",
        "condensed": "Educational content and delivery",
        "keywords": [
            "presentation",
            "workshop",
            "session",
            "content",
            "learning",
            "topics",
            "demo",
        ],
        "elements": [
            "Demonstration",
            "Gained Knowledge",
            "Open Discussion",
            "Panel Discussions",
            "Presentations",
            "Resources/Materials",
            "Session/Workshop",
            "Topics",
        ],
    },
    "People": {
        "description": "Feedback about specific people or groups at the conference",
        "condensed": "Specific people or groups at the conference",
        "keywords": [
            "speaker",
            "presenter",
            "staff",
            "organizer",
            "attendee",
            "expert",
            "consultant",
        ],
        "elements": [
            "Conference Staff",
            "Experts/Consultants",
            "Participants/Attendees",
            "Speakers/Presenters",
            "Unspecified Person",
        ],
    },
}


# =============================================================================
# ELEMENTS BY CATEGORY
# =============================================================================

ELEMENTS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Attendee Engagement & Interaction": {
        "Community": {
            "description": "Sense of belonging, community spirit, feeling welcomed, being part of a group, supportive environment",
            "condensed": "Sense of belonging and community spirit",
            "keywords": [
                "community",
                "belonging",
                "welcomed",
                "spirit",
                "inclusive",
                "supportive",
            ],
            "attributes": ["Inclusivity", "Atmosphere", "Welcoming"],
        },
        "Knowledge Exchange": {
            "description": "Sharing experiences with peers, learning from others' implementations, collaborative problem-solving, best practice sharing",
            "condensed": "Sharing experiences and learning from peers",
            "keywords": [
                "sharing",
                "exchange",
                "peers",
                "collaborative",
                "learn from others",
                "best practice",
            ],
            "attributes": ["Quality", "Relevance", "Engagement"],
        },
        "Networking": {
            "description": "Meeting new people, professional connections, peer discussions, contact exchange, relationship building",
            "condensed": "Meeting people and making professional connections",
            "keywords": [
                "networking",
                "connections",
                "meet",
                "professional",
                "peers",
                "contact",
            ],
            "attributes": ["Opportunities", "Quality", "Facilitation"],
        },
        "Social Events": {
            "description": "Gala dinners, receptions, evening events, informal gatherings, social activities outside sessions",
            "condensed": "Social activities and informal gatherings",
            "keywords": [
                "gala",
                "dinner",
                "reception",
                "social",
                "gathering",
                "party",
                "evening",
            ],
            "attributes": ["Quality", "Atmosphere", "Organization"],
        },
    },
    "Event Logistics & Infrastructure": {
        "Conference Application/Software": {
            "description": "Mobile apps, event platforms, Bluepulse app, digital tools for attendees, software for participation",
            "condensed": "Mobile apps and digital event tools",
            "keywords": ["app", "application", "software", "platform", "digital", "Bluepulse"],
            "attributes": ["Usability", "Features", "Reliability"],
        },
        "Conference Venue": {
            "description": "Location, rooms, facilities, seating, temperature, accessibility, physical space",
            "condensed": "Physical location and facilities",
            "keywords": [
                "venue",
                "location",
                "room",
                "facility",
                "seating",
                "accessibility",
                "temperature",
            ],
            "attributes": ["Accessibility", "Comfort", "Size", "Cleanliness", "Location"],
        },
        "Food/Beverages": {
            "description": "Meals, snacks, drinks, catering quality, dietary options, refreshments",
            "condensed": "Meals, snacks, and catering",
            "keywords": [
                "food",
                "lunch",
                "coffee",
                "snack",
                "catering",
                "beverage",
                "dietary",
                "drinks",
            ],
            "attributes": ["Quality", "Variety", "Dietary Options", "Availability"],
        },
        "Hotel": {
            "description": "Accommodation, lodging, hotel arrangements, room quality",
            "condensed": "Accommodation and lodging",
            "keywords": ["hotel", "accommodation", "lodging", "stay", "room"],
            "attributes": ["Quality", "Location", "Service", "Value"],
        },
        "Technological Tools": {
            "description": "A/V equipment, microphones, projectors, screens, tech setup for presentations",
            "condensed": "A/V equipment and tech setup",
            "keywords": ["AV", "microphone", "projector", "screen", "tech", "equipment"],
            "attributes": ["Quality", "Reliability", "Setup"],
        },
        "Transportation": {
            "description": "Getting to/from venue, shuttles, parking, travel arrangements, logistics of movement",
            "condensed": "Transportation and travel arrangements",
            "keywords": ["transportation", "shuttle", "parking", "travel", "bus", "taxi"],
            "attributes": ["Convenience", "Availability", "Cost"],
        },
        "Wi-Fi": {
            "description": "Internet connectivity, network access, connection quality",
            "condensed": "Internet connectivity",
            "keywords": ["wifi", "wi-fi", "internet", "network", "connectivity", "connection"],
            "attributes": ["Speed", "Reliability", "Availability"],
        },
    },
    "Event Operations & Management": {
        "Conference": {
            "description": "General event organization, overall management, event quality, hospitality, general conference experience",
            "condensed": "Overall event organization and quality",
            "keywords": [
                "conference",
                "event",
                "organization",
                "overall",
                "management",
                "hospitality",
            ],
            "attributes": ["Organization", "Quality", "Value"],
        },
        "Conference Registration": {
            "description": "Sign-up process, check-in, badge pickup, registration system, enrollment",
            "condensed": "Sign-up and check-in process",
            "keywords": [
                "registration",
                "check-in",
                "sign-up",
                "badge",
                "register",
                "enrollment",
            ],
            "attributes": ["Speed", "Ease", "Staff Helpfulness"],
        },
        "Conference Scheduling": {
            "description": "Session timing, agenda, time management, scheduling conflicts, program structure",
            "condensed": "Session timing and agenda management",
            "keywords": ["schedule", "timing", "agenda", "time", "slot", "conflict", "program"],
            "attributes": ["Pacing", "Breaks", "Conflicts", "Start/End Times"],
        },
        "Messaging & Awareness": {
            "description": "Communication, announcements, information clarity, signage, pre-event information",
            "condensed": "Communication and information clarity",
            "keywords": ["communication", "announcement", "information", "signage", "clarity"],
            "attributes": ["Clarity", "Timeliness", "Accessibility"],
        },
    },
    "Learning & Content Delivery": {
        "Demonstration": {
            "description": "Live demos, product showcases, hands-on examples, showing how things work",
            "condensed": "Live demos and product showcases",
            "keywords": ["demo", "demonstration", "showcase", "hands-on", "live", "showing"],
            "attributes": ["Quality", "Relevance", "Engagement"],
        },
        "Gained Knowledge": {
            "description": "What attendees learned, takeaways, actionable insights, things to implement",
            "condensed": "Learning takeaways and insights",
            "keywords": [
                "learned",
                "takeaway",
                "insight",
                "knowledge",
                "actionable",
                "implement",
            ],
            "attributes": ["Usefulness", "Applicability", "Depth"],
        },
        "Open Discussion": {
            "description": "Q&A sessions, audience participation, interactive discussions, roundtables",
            "condensed": "Q&A and audience participation",
            "keywords": [
                "Q&A",
                "question",
                "discussion",
                "interactive",
                "participation",
                "roundtable",
            ],
            "attributes": ["Quality", "Time Allocation", "Facilitation"],
        },
        "Panel Discussions": {
            "description": "Panel format sessions, multi-speaker discussions, panel quality",
            "condensed": "Panel format sessions",
            "keywords": ["panel", "panelist", "multi-speaker", "discussion"],
            "attributes": ["Quality", "Diversity", "Moderation"],
        },
        "Presentations": {
            "description": "Individual talks, keynotes, speaker presentations, talk quality and content",
            "condensed": "Individual talks and keynotes",
            "keywords": ["presentation", "talk", "keynote", "speech", "lecture"],
            "attributes": ["Content Quality", "Delivery", "Relevance"],
        },
        "Resources/Materials": {
            "description": "Handouts, slides, documentation, learning materials, presentation copies",
            "condensed": "Handouts and learning materials",
            "keywords": [
                "handout",
                "slides",
                "material",
                "documentation",
                "resources",
                "copies",
            ],
            "attributes": ["Quality", "Availability", "Usefulness"],
        },
        "Session/Workshop": {
            "description": "Breakout sessions, workshops, training sessions, hands-on learning",
            "condensed": "Breakout sessions and workshops",
            "keywords": ["session", "workshop", "breakout", "training", "hands-on"],
            "attributes": ["Content Quality", "Interactivity", "Duration"],
        },
        "Topics": {
            "description": "Subject matter, themes, content relevance, topic selection, what was covered",
            "condensed": "Subject matter and themes",
            "keywords": ["topic", "subject", "theme", "content", "relevance"],
            "attributes": ["Relevance", "Variety", "Depth"],
        },
    },
    "People": {
        "Conference Staff": {
            "description": "Organizers, volunteers, support staff, event team, Explorance team (when mentioned as organizers/hosts)",
            "condensed": "Organizers and support staff",
            "keywords": [
                "staff",
                "organizer",
                "volunteer",
                "team",
                "support",
                "Explorance team",
            ],
            "attributes": ["Helpfulness", "Friendliness", "Responsiveness"],
        },
        "Experts/Consultants": {
            "description": "Industry experts, product specialists, consultants, Explorance experts (when mentioned for their expertise)",
            "condensed": "Industry experts and consultants",
            "keywords": ["expert", "consultant", "specialist", "advisor", "Explorance experts"],
            "attributes": ["Knowledge", "Helpfulness", "Availability"],
        },
        "Participants/Attendees": {
            "description": "Fellow attendees, other conference-goers, peers at the conference, Blue users, community members",
            "condensed": "Fellow attendees",
            "keywords": [
                "attendee",
                "participant",
                "peer",
                "colleague",
                "Blue users",
                "community members",
            ],
            "attributes": ["Engagement", "Diversity", "Professionalism"],
        },
        "Speakers/Presenters": {
            "description": "Keynote speakers, session presenters, panelists, people giving talks",
            "condensed": "Keynote speakers and presenters",
            "keywords": ["speaker", "presenter", "keynote", "panelist"],
            "attributes": ["Knowledge", "Presentation Skills", "Engagement", "Approachability"],
        },
        "Unspecified Person": {
            "description": "References to people without clear role identification",
            "condensed": "People without clear role",
            "keywords": ["someone", "person", "they", "people"],
            "attributes": ["Helpfulness", "Interaction Quality"],
        },
    },
}


# =============================================================================
# STAGE 1 EXAMPLES (Category Detection)
# =============================================================================

STAGE1_EXAMPLES: List[Dict[str, Any]] = [
    {
        "text": "The networking sessions were fantastic and I made great connections with peers from other institutions.",
        "output": {
            "categories_present": ["Attendee Engagement & Interaction"],
            "has_classifiable_content": True,
            "reasoning": "Discusses networking and peer connections",
        },
    },
    {
        "text": "The WiFi kept dropping during sessions and the room was too cold.",
        "output": {
            "categories_present": ["Event Logistics & Infrastructure"],
            "has_classifiable_content": True,
            "reasoning": "Mentions WiFi connectivity and venue temperature issues",
        },
    },
    {
        "text": "The keynote speaker was brilliant and the presentation on machine learning was very insightful.",
        "output": {
            "categories_present": ["Learning & Content Delivery", "People"],
            "has_classifiable_content": True,
            "reasoning": "Discusses both the presentation content and the speaker",
        },
    },
    {
        "text": "The conference was well organized but I wish there were more hands-on workshops. The Explorance team was very helpful.",
        "output": {
            "categories_present": [
                "Event Operations & Management",
                "Learning & Content Delivery",
                "People",
            ],
            "has_classifiable_content": True,
            "reasoning": "Covers organization quality, workshop content request, and staff praise",
        },
    },
    {
        "text": "I loved connecting with the Blue community and sharing knowledge with other users.",
        "output": {
            "categories_present": ["Attendee Engagement & Interaction"],
            "has_classifiable_content": True,
            "reasoning": "Discusses community connection and knowledge sharing among attendees",
        },
    },
    {
        "text": "The registration process was slow and confusing.",
        "output": {
            "categories_present": ["Event Operations & Management"],
            "has_classifiable_content": True,
            "reasoning": "Feedback about registration process",
        },
    },
    {
        "text": "Seeing is believing!",
        "output": {
            "categories_present": ["Event Operations & Management"],
            "has_classifiable_content": True,
            "reasoning": "Vague positive sentiment about the conference overall",
        },
    },
    {
        "text": "Data integrity never goes out of style.",
        "output": {
            "categories_present": [],
            "has_classifiable_content": False,
            "reasoning": "General statement not specifically about conference feedback",
        },
    },
    {
        "text": "The food was excellent and there were plenty of vegetarian options.",
        "output": {
            "categories_present": ["Event Logistics & Infrastructure"],
            "has_classifiable_content": True,
            "reasoning": "Feedback about catering and dietary options",
        },
    },
    {
        "text": "Great demo of the new analytics features! The product team really knows their stuff.",
        "output": {
            "categories_present": ["Learning & Content Delivery", "People"],
            "has_classifiable_content": True,
            "reasoning": "Discusses demonstration content and the people who presented",
        },
    },
]


# =============================================================================
# STAGE 1 RULES
# =============================================================================

STAGE1_RULES: List[str] = [
    "A comment can belong to MULTIPLE categories if it discusses multiple aspects.",
    "Focus on what the comment is ABOUT, not just words mentioned.",
    "'Community' refers to the feeling of belonging; 'Networking' refers to the act of meeting people.",
    "'Presentations' = talk quality/content; 'Speakers/Presenters' = the people themselves.",
    "General praise like 'great conference' without specifics → Event Operations & Management > Conference.",
    "If a comment mentions both the content AND the presenter, include BOTH categories.",
    "Food, venue, WiFi, hotel, transportation → Event Logistics & Infrastructure",
    "Registration, scheduling, communication, organization → Event Operations & Management",
    "If feedback is not specifically about the conference experience, mark has_classifiable_content as false",
]


# =============================================================================
# STAGE 2 EXAMPLES (Element Extraction) - By Category
# Battle-tested examples from production prompts
# =============================================================================

STAGE2_EXAMPLES: Dict[str, List[Dict[str, Any]]] = {
    "Attendee Engagement & Interaction": [
        {
            "text": "The community is so supportive and open to sharing their knowledge.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The community is so supportive",
                        "reasoning": "Expresses feeling of supportive community environment",
                        "element": "Community",
                        "sentiment": "positive",
                    },
                    {
                        "excerpt": "open to sharing their knowledge",
                        "reasoning": "References peer knowledge sharing",
                        "element": "Knowledge Exchange",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "Change the networking session. Nobody from Explorance showed up at my table. Sitting there with 1 other person was awkward.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "Change the networking session. Nobody from Explorance showed up at my table. Sitting there with 1 other person was awkward",
                        "reasoning": "Negative experience with networking session format",
                        "element": "Networking",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "I would have liked to go to the Marina for the gala dinner but I understand that would have been challenging.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "I would have liked to go to the Marina for the gala dinner",
                        "reasoning": "Suggestion about gala dinner venue",
                        "element": "Social Events",
                        "sentiment": "mixed",
                    },
                ],
            },
        },
        {
            "text": "It only took an hour to go from brand new user to genuinely feeling like a part of the Blue community.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "genuinely feeling like a part of the Blue community",
                        "reasoning": "Expresses sense of belonging to community",
                        "element": "Community",
                        "sentiment": "positive",
                    },
                ],
            },
        },
    ],
    "Event Logistics & Infrastructure": [
        {
            "text": "Having the Bluepulse app information earlier. Those without a Smart phone were not able to evaluate the sessions.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "Having the Bluepulse app information earlier. Those without a Smart phone were not able to evaluate the sessions",
                        "reasoning": "Feedback about conference app accessibility and communication",
                        "element": "Conference Application/Software",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "Wish there was hand sanitizer more available around the conference.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "Wish there was hand sanitizer more available around the conference",
                        "reasoning": "Request for venue amenity",
                        "element": "Conference Venue",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "have drinks available, even if a cash bar, at events.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "have drinks available, even if a cash bar, at events",
                        "reasoning": "Request for beverage availability",
                        "element": "Food/Beverages",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "The WiFi kept dropping and made it hard to follow along.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The WiFi kept dropping and made it hard to follow along",
                        "reasoning": "Complaint about internet connectivity",
                        "element": "Wi-Fi",
                        "sentiment": "negative",
                    },
                ],
            },
        },
    ],
    "Event Operations & Management": [
        {
            "text": "An excellent, informative, and well-organised event.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "An excellent, informative, and well-organised event",
                        "reasoning": "General positive feedback about event organization",
                        "element": "Conference",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "The registration process was rather slow, I did sign up quite close to the date but I never even got an invoice.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The registration process was rather slow, I did sign up quite close to the date but I never even got an invoice",
                        "reasoning": "Complaint about registration process and invoicing",
                        "element": "Conference Registration",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "More repeated sessions which, while not bad, the time could have been spent doing more hands-on activities.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "More repeated sessions which, while not bad, the time could have been spent doing more hands-on activities",
                        "reasoning": "Feedback about session scheduling and program structure",
                        "element": "Conference Scheduling",
                        "sentiment": "mixed",
                    },
                ],
            },
        },
        {
            "text": "BNG 2022 has set the bar high in terms of hospitality. They go beyond their call for duty.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "BNG 2022 has set the bar high in terms of hospitality. They go beyond their call for duty",
                        "reasoning": "Praise for conference hospitality and management",
                        "element": "Conference",
                        "sentiment": "positive",
                    },
                ],
            },
        },
    ],
    "Learning & Content Delivery": [
        {
            "text": "The presentations were better than the panel discussion. Better panelists would be preferred.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The presentations were better than the panel discussion",
                        "reasoning": "Comparison of presentation vs panel format quality",
                        "element": "Presentations",
                        "sentiment": "positive",
                    },
                    {
                        "excerpt": "Better panelists would be preferred",
                        "reasoning": "Criticism of panel discussion quality",
                        "element": "Panel Discussions",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "Provide presentation materials hard or soft copies.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "Provide presentation materials hard or soft copies",
                        "reasoning": "Request for presentation materials/handouts",
                        "element": "Resources/Materials",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "More technical workshops would be great. The presentations were good.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "More technical workshops would be great",
                        "reasoning": "Request for more workshop sessions",
                        "element": "Session/Workshop",
                        "sentiment": "mixed",
                    },
                    {
                        "excerpt": "The presentations were good",
                        "reasoning": "Positive feedback on presentations",
                        "element": "Presentations",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "I came away with a significant 'to do' list which will help us leverage insights collected from our students.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "I came away with a significant 'to do' list which will help us leverage insights collected from our students",
                        "reasoning": "Actionable takeaways gained from conference",
                        "element": "Gained Knowledge",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "I wonder if some round table discussions would help.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "I wonder if some round table discussions would help",
                        "reasoning": "Suggestion for open discussion format",
                        "element": "Open Discussion",
                        "sentiment": "mixed",
                    },
                ],
            },
        },
        {
            "text": "high quality papers and mix of topics from increasing response rates through to machine learning applied to text analytics",
            "output": {
                "classifications": [
                    {
                        "excerpt": "high quality papers and mix of topics from increasing response rates through to machine learning applied to text analytics",
                        "reasoning": "Praise for topic variety and quality",
                        "element": "Topics",
                        "sentiment": "positive",
                    },
                ],
            },
        },
    ],
    "People": [
        {
            "text": "The Explorance staff are so genuine, knowledgeable, and accessible.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The Explorance staff are so genuine, knowledgeable, and accessible",
                        "reasoning": "Praise for conference staff qualities",
                        "element": "Conference Staff",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "The ability to talk not only to Explorance Experts but to network with community members made this valuable.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "talk not only to Explorance Experts",
                        "reasoning": "Reference to product experts",
                        "element": "Experts/Consultants",
                        "sentiment": "positive",
                    },
                    {
                        "excerpt": "network with community members",
                        "reasoning": "Reference to fellow attendees",
                        "element": "Participants/Attendees",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "The Blue users you'll meet are smart, creative, and always willing to share and collaborate.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "The Blue users you'll meet are smart, creative, and always willing to share and collaborate",
                        "reasoning": "Praise for fellow attendees",
                        "element": "Participants/Attendees",
                        "sentiment": "positive",
                    },
                ],
            },
        },
        {
            "text": "some speakers appeared to have changed or modified the presentation from the original abstract",
            "output": {
                "classifications": [
                    {
                        "excerpt": "some speakers appeared to have changed or modified the presentation from the original abstract",
                        "reasoning": "Criticism of speakers deviating from abstract",
                        "element": "Speakers/Presenters",
                        "sentiment": "negative",
                    },
                ],
            },
        },
        {
            "text": "Nobody from Explorance showed up at my table.",
            "output": {
                "classifications": [
                    {
                        "excerpt": "Nobody from Explorance showed up at my table",
                        "reasoning": "Complaint about staff absence at networking",
                        "element": "Conference Staff",
                        "sentiment": "negative",
                    },
                ],
            },
        },
    ],
}


# =============================================================================
# STAGE 2 RULES - By Category
# Battle-tested rules from production prompts
# =============================================================================

STAGE2_RULES: Dict[str, List[str]] = {
    "Attendee Engagement & Interaction": [
        "Extract the EXACT excerpt from the comment that relates to each element.",
        "Each excerpt should be classified to ONE element only.",
        "Sentiment: positive (praise), negative (criticism), neutral (observation), mixed (both positive and negative).",
        "'Community' = feeling of belonging; 'Networking' = act of meeting/connecting.",
        "'Knowledge Exchange' = peer-to-peer learning; different from formal presentations.",
    ],
    "Event Logistics & Infrastructure": [
        "Extract the EXACT excerpt from the comment that relates to each element.",
        "Each excerpt should be classified to ONE element only.",
        "Sentiment: positive (praise), negative (criticism), neutral (observation), mixed (both positive and negative).",
        "'Conference Application/Software' = apps for attendees; 'Technological Tools' = A/V equipment for sessions.",
    ],
    "Event Operations & Management": [
        "Extract the EXACT excerpt from the comment that relates to each element.",
        "Each excerpt should be classified to ONE element only.",
        "Sentiment: positive (praise), negative (criticism), neutral (observation), mixed (both positive and negative).",
        "General praise like 'great conference' or 'well organized' → Conference element.",
        "Comments about session timing or agenda structure → Conference Scheduling.",
    ],
    "Learning & Content Delivery": [
        "Extract the EXACT excerpt from the comment that relates to each element.",
        "Each excerpt should be classified to ONE element only.",
        "Sentiment: positive (praise), negative (criticism), neutral (observation), mixed (both positive and negative).",
        "'Presentations' = quality of talks; 'Topics' = what subjects were covered.",
        "'Session/Workshop' = format of learning; 'Gained Knowledge' = what was learned.",
        "Requests for 'more workshops' or 'hands-on sessions' → Session/Workshop.",
    ],
    "People": [
        "Extract the EXACT excerpt from the comment that relates to each element.",
        "Each excerpt should be classified to ONE element only.",
        "Sentiment: positive (praise), negative (criticism), neutral (observation), mixed (both positive and negative).",
        "'Explorance team' as hosts/organizers → Conference Staff.",
        "'Explorance experts' for knowledge/consulting → Experts/Consultants.",
        "'Blue users' or 'community members' → Participants/Attendees.",
        "Named speakers or 'the presenter' → Speakers/Presenters.",
    ],
}


# =============================================================================
# HANDCRAFTED CONTENT PROVIDER CLASS
# =============================================================================


class HandcraftedContentProvider(ContentProvider):
    """
    Provides content from the handcrafted definitions above.

    This is the PRIMARY content source - battle-tested and reliable.

    Usage:
        provider = HandcraftedContentProvider()
        categories = provider.get_categories()
        examples = provider.get_examples("stage1")
    """

    def get_categories(self) -> List[CategoryContent]:
        """Get all handcrafted category definitions."""
        return [
            CategoryContent(
                name=name,
                description=data["description"],
                condensed_description=data.get("condensed", ""),
                keywords=data.get("keywords", []),
                elements=data.get("elements", []),
            )
            for name, data in CATEGORIES.items()
        ]

    def get_elements(self, category: str) -> List[ElementContent]:
        """Get elements for a category."""
        if category not in ELEMENTS:
            return []

        return [
            ElementContent(
                name=name,
                category=category,
                description=data["description"],
                condensed_description=data.get("condensed", ""),
                keywords=data.get("keywords", []),
                attributes=data.get("attributes", []),
            )
            for name, data in ELEMENTS[category].items()
        ]

    def get_attributes(self, category: str, element: str) -> List[AttributeContent]:
        """Get attributes for an element."""
        if category not in ELEMENTS or element not in ELEMENTS[category]:
            return []

        element_data = ELEMENTS[category][element]
        return [
            AttributeContent(
                name=attr_name,
                element=element,
                category=category,
                description=f"Attribute: {attr_name}",
                condensed_description=attr_name,
            )
            for attr_name in element_data.get("attributes", [])
        ]

    def get_examples(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Example]:
        """Get handcrafted examples for a stage."""

        if stage == "stage1":
            return [
                Example(
                    text=ex["text"],
                    output=ex["output"],
                    stage="stage1",
                )
                for ex in STAGE1_EXAMPLES
            ]

        elif stage == "stage2":
            if category is None:
                # Return all stage2 examples
                examples = []
                for cat, cat_examples in STAGE2_EXAMPLES.items():
                    for ex in cat_examples:
                        examples.append(
                            Example(
                                text=ex["text"],
                                output=ex["output"],
                                stage="stage2",
                                category=cat,
                            )
                        )
                return examples
            else:
                # Return examples for specific category
                cat_examples = STAGE2_EXAMPLES.get(category, [])
                return [
                    Example(
                        text=ex["text"],
                        output=ex["output"],
                        stage="stage2",
                        category=category,
                    )
                    for ex in cat_examples
                ]

        # Stage 3 typically uses generated content, but can be added here
        return []

    def get_rules(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Rule]:
        """Get handcrafted rules for a stage."""

        if stage == "stage1":
            return [Rule(rule_text=rule, stage="stage1") for rule in STAGE1_RULES]

        elif stage == "stage2":
            if category is None:
                # Return all stage2 rules
                rules = []
                for cat, cat_rules in STAGE2_RULES.items():
                    for rule in cat_rules:
                        rules.append(Rule(rule_text=rule, stage="stage2", category=cat))
                return rules
            else:
                # Return rules for specific category
                cat_rules = STAGE2_RULES.get(category, [])
                return [
                    Rule(rule_text=rule, stage="stage2", category=category)
                    for rule in cat_rules
                ]

        return []
