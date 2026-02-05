"""
Handcrafted Content Provider

This module contains battle-tested, manually curated content for the classifier.
It serves as the PRIMARY content source - the gold standard.

Structure:
- CATEGORIES: Category definitions with descriptions
- STAGE1_EXAMPLES: Proven examples for category detection
- STAGE1_RULES: Disambiguation rules for category detection
- STAGE2_EXAMPLES: Proven examples for element extraction (by category)
- STAGE2_RULES: Rules for element extraction
- (Stage 3 typically uses generated content, but can be added here)

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
    "People": {
        "description": "Feedback about individuals involved in the conference",
        "condensed": "People involved (speakers, organizers, staff, attendees)",
        "keywords": ["speaker", "presenter", "organizer", "staff", "volunteer", "attendee"],
        "elements": [
            "Speakers/Presenters",
            "Organizers",
            "Staff/Volunteers",
            "Other Attendees",
        ],
    },
    "Event Logistics": {
        "description": "Feedback about practical aspects of attending the event",
        "condensed": "Practical/logistical aspects (venue, registration, scheduling)",
        "keywords": ["venue", "location", "registration", "schedule", "timing", "wifi", "food"],
        "elements": [
            "Venue",
            "Registration",
            "Scheduling",
            "Wi-Fi/Technology",
            "Food & Beverage",
        ],
    },
    "Learning & Content Delivery": {
        "description": "Feedback about the educational content and how it was delivered",
        "condensed": "Content quality and delivery (presentations, workshops, materials)",
        "keywords": [
            "presentation",
            "workshop",
            "content",
            "learning",
            "session",
            "talk",
            "material",
        ],
        "elements": [
            "Presentations",
            "Workshops",
            "Panel Discussions",
            "Materials",
            "Q&A Sessions",
        ],
    },
    "Networking & Social": {
        "description": "Feedback about opportunities to connect with others",
        "condensed": "Social and networking aspects (events, opportunities, community)",
        "keywords": ["networking", "social", "connect", "meet", "community", "event"],
        "elements": [
            "Networking Events",
            "Social Events",
            "Community Building",
            "Collaboration Opportunities",
        ],
    },
    "Overall Experience": {
        "description": "General impressions and holistic feedback about the conference",
        "condensed": "General experience and overall impressions",
        "keywords": ["overall", "general", "experience", "impression", "conference", "event"],
        "elements": [
            "General Satisfaction",
            "Value for Money",
            "Likelihood to Return",
            "Recommendations",
        ],
    },
}


# =============================================================================
# ELEMENTS BY CATEGORY
# =============================================================================

ELEMENTS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "People": {
        "Speakers/Presenters": {
            "description": "Individuals who gave talks, presentations, or led sessions",
            "condensed": "Talk/session presenters",
            "keywords": ["speaker", "presenter", "keynote", "talk"],
            "attributes": ["Knowledge", "Presentation Skills", "Engagement", "Approachability"],
        },
        "Organizers": {
            "description": "People responsible for planning and running the conference",
            "condensed": "Event planners and coordinators",
            "keywords": ["organizer", "coordinator", "planner"],
            "attributes": ["Responsiveness", "Organization", "Communication"],
        },
        "Staff/Volunteers": {
            "description": "Support staff and volunteers helping at the event",
            "condensed": "Support staff and volunteers",
            "keywords": ["staff", "volunteer", "helper", "assistant"],
            "attributes": ["Helpfulness", "Friendliness", "Availability"],
        },
        "Other Attendees": {
            "description": "Fellow conference participants",
            "condensed": "Fellow participants",
            "keywords": ["attendee", "participant", "audience", "peer"],
            "attributes": ["Engagement", "Diversity", "Professionalism"],
        },
    },
    "Event Logistics": {
        "Venue": {
            "description": "The physical location and facilities",
            "condensed": "Physical space and facilities",
            "keywords": ["venue", "location", "building", "room", "space"],
            "attributes": ["Accessibility", "Comfort", "Size", "Cleanliness"],
        },
        "Registration": {
            "description": "The sign-up and check-in process",
            "condensed": "Sign-up and check-in",
            "keywords": ["registration", "check-in", "sign-up", "badge"],
            "attributes": ["Speed", "Ease", "Staff Helpfulness"],
        },
        "Scheduling": {
            "description": "Timing and organization of sessions",
            "condensed": "Session timing and breaks",
            "keywords": ["schedule", "timing", "agenda", "break", "slot"],
            "attributes": ["Pacing", "Breaks", "Conflicts", "Start/End Times"],
        },
        "Wi-Fi/Technology": {
            "description": "Internet connectivity and tech support",
            "condensed": "Internet and tech support",
            "keywords": ["wifi", "wi-fi", "internet", "tech", "AV", "microphone"],
            "attributes": ["Reliability", "Speed", "Support"],
        },
        "Food & Beverage": {
            "description": "Meals, snacks, and drinks provided",
            "condensed": "Meals and refreshments",
            "keywords": ["food", "lunch", "coffee", "snack", "catering", "beverage"],
            "attributes": ["Quality", "Variety", "Dietary Options", "Availability"],
        },
    },
    # Add more categories' elements as needed...
}


# =============================================================================
# STAGE 1 EXAMPLES (Category Detection)
# =============================================================================

STAGE1_EXAMPLES: List[Dict[str, Any]] = [
    {
        "text": "The keynote speaker was absolutely brilliant. Her insights on AI were groundbreaking.",
        "output": {
            "categories_present": ["People", "Learning & Content Delivery"],
            "reasoning": "Discusses a speaker (People) and the content of their talk (Learning & Content Delivery)",
        },
    },
    {
        "text": "WiFi kept dropping during the sessions and the venue was too cold.",
        "output": {
            "categories_present": ["Event Logistics"],
            "reasoning": "Discusses technical issues (WiFi) and venue conditions - both are logistics",
        },
    },
    {
        "text": "I loved the networking dinner! Met so many interesting people in my field.",
        "output": {
            "categories_present": ["Networking & Social"],
            "reasoning": "Discusses a social event and meeting people - networking focused",
        },
    },
    {
        "text": "Overall, this was the best conference I've attended in years. Totally worth the price.",
        "output": {
            "categories_present": ["Overall Experience"],
            "reasoning": "General evaluation of the entire conference experience",
        },
    },
    {
        "text": "The workshop materials were outdated, and the presenter seemed unprepared.",
        "output": {
            "categories_present": ["Learning & Content Delivery", "People"],
            "reasoning": "Discusses content quality (materials) and presenter preparation",
        },
    },
    {
        "text": "Registration was a breeze - got my badge in under a minute!",
        "output": {
            "categories_present": ["Event Logistics"],
            "reasoning": "Specifically about the registration process - a logistical aspect",
        },
    },
    {
        "text": "Not enough vegetarian options at lunch.",
        "output": {
            "categories_present": ["Event Logistics"],
            "reasoning": "Food-related feedback falls under logistics",
        },
    },
    {
        "text": "The Q&A sessions were too short. Just when discussions got interesting, they cut us off.",
        "output": {
            "categories_present": ["Learning & Content Delivery", "Event Logistics"],
            "reasoning": "Discusses Q&A quality (content delivery) and time constraints (scheduling/logistics)",
        },
    },
]


# =============================================================================
# STAGE 1 RULES
# =============================================================================

STAGE1_RULES: List[str] = [
    "If feedback mentions both a person AND their content/delivery, mark BOTH 'People' AND 'Learning & Content Delivery'",
    "General satisfaction statements ('great conference', 'would recommend') → 'Overall Experience'",
    "Food, venue, WiFi, registration, scheduling → 'Event Logistics' (even if people are mentioned serving food)",
    "If networking is mentioned alongside content discussions, consider if it's social (→ Networking) or content-focused (→ Learning)",
    "Staff helpfulness at registration → 'Event Logistics' (not 'People', unless specifically praising an individual)",
]


# =============================================================================
# STAGE 2 EXAMPLES (Element Extraction) - By Category
# =============================================================================

STAGE2_EXAMPLES: Dict[str, List[Dict[str, Any]]] = {
    "People": [
        {
            "text": "The keynote speaker was amazing, really knew her stuff.",
            "output": {
                "elements": [
                    {
                        "element": "Speakers/Presenters",
                        "sentiment": "positive",
                        "confidence": 5,
                    },
                ],
            },
        },
        {
            "text": "Volunteers were helpful but the organizers seemed stressed and hard to reach.",
            "output": {
                "elements": [
                    {"element": "Staff/Volunteers", "sentiment": "positive", "confidence": 4},
                    {"element": "Organizers", "sentiment": "negative", "confidence": 4},
                ],
            },
        },
    ],
    "Event Logistics": [
        {
            "text": "Venue was beautiful but the WiFi was terrible.",
            "output": {
                "elements": [
                    {"element": "Venue", "sentiment": "positive", "confidence": 5},
                    {"element": "Wi-Fi/Technology", "sentiment": "negative", "confidence": 5},
                ],
            },
        },
        {
            "text": "Lunch was decent, nice variety of options.",
            "output": {
                "elements": [
                    {"element": "Food & Beverage", "sentiment": "positive", "confidence": 4},
                ],
            },
        },
        {
            "text": "Too many sessions at the same time, had to miss several I wanted to attend.",
            "output": {
                "elements": [
                    {"element": "Scheduling", "sentiment": "negative", "confidence": 5},
                ],
            },
        },
    ],
    "Learning & Content Delivery": [
        {
            "text": "The workshops were hands-on and practical. Learned so much!",
            "output": {
                "elements": [
                    {"element": "Workshops", "sentiment": "positive", "confidence": 5},
                ],
            },
        },
        {
            "text": "Presentations were too basic for the advertised audience level.",
            "output": {
                "elements": [
                    {"element": "Presentations", "sentiment": "negative", "confidence": 4},
                ],
            },
        },
    ],
}


# =============================================================================
# STAGE 2 RULES - By Category
# =============================================================================

STAGE2_RULES: Dict[str, List[str]] = {
    "People": [
        "If 'speaker' is mentioned in context of their talk quality, focus on Speakers/Presenters",
        "Generic 'staff' without context → Staff/Volunteers",
        "Mentions of 'the team' or 'they' in organizational context → Organizers",
    ],
    "Event Logistics": [
        "'Tech issues' during presentations → Wi-Fi/Technology (not Presentations)",
        "Complaints about seating → Venue",
        "'Breaks' can mean Scheduling (timing) or Venue (break room quality) - use context",
    ],
    "Learning & Content Delivery": [
        "If discussing hands-on activities → Workshops",
        "If discussing seated talks → Presentations",
        "Panel-specific feedback → Panel Discussions",
        "Handouts, slides shared after → Materials",
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
                description=f"Attribute: {attr_name}",  # Simplified - can be expanded
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

        # Stage 3 typically uses generated content
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
