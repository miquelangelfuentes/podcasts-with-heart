"""
Podcast Script Parser for Podcasts with Heart.
Parses .txt scripts containing metadata, speaker declarations,
spatial stereo panning, pauses, and dialogue cues.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class SpeakerConfig:
    name: str
    voice_id: str = "af_heart"       # Default voice ID
    pan: float = 0.0                 # -1.0 (full left) to +1.0 (full right)
    speed: float = 1.0               # 0.5 to 2.0
    pitch: float = 0.0               # -5 to +5
    description: str = ""

@dataclass
class PodcastSegment:
    segment_type: str                # 'dialogue', 'pause', 'cue'
    speaker: str = ""
    text: str = ""
    pause_ms: int = 400
    pan: float = 0.0
    speed: float = 1.0
    pitch: float = 0.0
    voice_id: str = "af_heart"
    raw_line: str = ""

@dataclass
class PodcastScript:
    title: str = "Educational Podcast"
    description: str = ""
    format_info: str = "Stereo 160kbps"
    default_pause_ms: int = 350
    turn_pause_ms: int = 650
    metadata: Dict[str, str] = field(default_factory=dict)
    speakers: Dict[str, SpeakerConfig] = field(default_factory=dict)
    segments: List[PodcastSegment] = field(default_factory=list)

class ScriptParser:
    """Robust parser for podcast script text files."""

    DEFAULT_VOICE_MAP = {
        0: "af_heart",   # US Female, Flagship Studio Heart voice
        1: "am_adam",    # US Male, dynamic and resonant
        2: "bf_emma",    # UK Female, refined storyteller
        3: "af_bella",   # US Female, warm and natural
        4: "bm_george",  # UK Male, articulate narrator
        5: "af_sky",     # US Female, lively and fresh
        6: "bm_lewis",   # UK Male, distinct storytelling
        7: "af_nicole",  # US Female, conversational
    }

    def __init__(self):
        pass

    def parse_time_ms(self, time_str: str) -> int:
        """Converts strings like '500ms', '1.5s', '800' into milliseconds."""
        time_str = time_str.strip().lower()
        if time_str.endswith("ms"):
            try:
                return int(float(time_str[:-2]))
            except ValueError:
                return 400
        elif time_str.endswith("s"):
            try:
                return int(float(time_str[:-1]) * 1000)
            except ValueError:
                return 1000
        else:
            try:
                return int(float(time_str))
            except ValueError:
                return 400

    def parse_pan(self, pan_str: str) -> float:
        """Parses panning values like '-25%', '0.25', 'left', 'center', 'right'."""
        pan_str = pan_str.strip().lower()
        if pan_str in ("left", "l", "esquerra"):
            return -0.4
        elif pan_str in ("right", "r", "dreta"):
            return 0.4
        elif pan_str in ("center", "centre", "c"):
            return 0.0
        elif pan_str.endswith("%"):
            try:
                val = float(pan_str[:-1])
                return max(-1.0, min(1.0, val / 100.0))
            except ValueError:
                return 0.0
        else:
            try:
                val = float(pan_str)
                return max(-1.0, min(1.0, val))
            except ValueError:
                return 0.0

    def parse(self, text_content: str) -> PodcastScript:
        """Parses full script content into structured PodcastScript dataclass."""
        lines = text_content.splitlines()
        script = PodcastScript()

        mode = "HEADER"
        assigned_voice_idx = 0
        default_voices = ["jenny", "guy", "aria", "davis", "sonia", "ryan", "libby", "natasha"]
        default_pans = [-0.25, 0.25, 0.0, -0.35, 0.35]

        dialogue_pattern = re.compile(r"^([A-Za-z0-9_\-\.\s]+?)\s*:\s*(.*)$")
        bracket_tag_pattern = re.compile(r"^\[([A-Z_]+)(?:\s*:\s*([^\]]+))?\]", re.IGNORECASE)

        last_speaker = None

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            # Standard separators marking the start of dialogue
            if line.startswith("---") or line.startswith("===") or line.startswith("***"):
                mode = "DIALOGUE"
                continue

            tag_match = bracket_tag_pattern.match(line)
            if tag_match:
                tag_name = tag_match.group(1).upper()
                tag_val = tag_match.group(2).strip() if tag_match.group(2) else ""

                if tag_name in ("SPEAKERS", "VOICES", "CAST", "LOCUTORS", "VEUS"):
                    mode = "SPEAKERS_DESC"
                    continue
                elif tag_name in ("SPEAKERS_CONFIG", "VOICE_CONFIG", "CONFIG", "CONFIGURACIO_VOICES", "CONFIGURACIO_VEUS"):
                    mode = "SPEAKERS_CONFIG"
                    continue
                elif tag_name in ("SCRIPT", "DIALOGUE", "CONTENT", "PODCAST", "GUIO", "DIALEG"):
                    mode = "DIALOGUE"
                    continue

                if tag_name in ("PAUSE", "PAUSA"):
                    pause_ms = self.parse_time_ms(tag_val) if tag_val else script.default_pause_ms
                    if mode == "DIALOGUE":
                        script.segments.append(PodcastSegment(
                            segment_type="pause",
                            pause_ms=pause_ms,
                            raw_line=raw_line
                        ))
                    continue

                if tag_name in ("MUSIC", "EFFECT", "FX", "SOUND", "CUE", "MUSICA"):
                    if mode == "DIALOGUE":
                        script.segments.append(PodcastSegment(
                            segment_type="pause",
                            pause_ms=500,
                            raw_line=raw_line
                        ))
                    continue

                if mode != "DIALOGUE":
                    script.metadata[tag_name] = tag_val
                    if tag_name in ("TITLE", "TITOL"):
                        script.title = tag_val
                    elif tag_name in ("DESCRIPTION", "DESCRIPCIO"):
                        script.description = tag_val
                    elif tag_name in ("FORMAT",):
                        script.format_info = tag_val
                    elif tag_name in ("DEFAULT_PAUSE", "PAUSA_DEFECTE"):
                        script.default_pause_ms = self.parse_time_ms(tag_val)
                    elif tag_name in ("INTERLOCUTOR_PAUSE", "TURN_PAUSE", "PAUSA_INTERLOCUCIO", "PAUSA_INTERLOCUTOR"):
                        script.turn_pause_ms = self.parse_time_ms(tag_val)
                    continue

            # Section: Speaker descriptions (- Host: description)
            if mode == "SPEAKERS_DESC":
                item_match = re.match(r"^[-*]\s*([^:]+?)\s*:\s*(.*)$", line)
                if item_match:
                    spk_name = item_match.group(1).strip()
                    spk_desc = item_match.group(2).strip()
                    if spk_name not in script.speakers:
                        v_id = default_voices[assigned_voice_idx % len(default_voices)]
                        p_val = default_pans[assigned_voice_idx % len(default_pans)]
                        assigned_voice_idx += 1
                        script.speakers[spk_name] = SpeakerConfig(
                            name=spk_name,
                            voice_id=v_id,
                            pan=p_val,
                            description=spk_desc
                        )
                    else:
                        script.speakers[spk_name].description = spk_desc
                    continue

            # Section: Speaker config (Speaker: voice=jenny pan=-25% speed=1.0)
            if mode == "SPEAKERS_CONFIG":
                cfg_match = dialogue_pattern.match(line)
                if cfg_match:
                    spk_name = cfg_match.group(1).strip()
                    params_str = cfg_match.group(2).strip()
                    
                    if spk_name not in script.speakers:
                        v_id = default_voices[assigned_voice_idx % len(default_voices)]
                        p_val = default_pans[assigned_voice_idx % len(default_pans)]
                        assigned_voice_idx += 1
                        script.speakers[spk_name] = SpeakerConfig(name=spk_name, voice_id=v_id, pan=p_val)

                    spk_cfg = script.speakers[spk_name]

                    for p in params_str.split():
                        if "=" in p:
                            k, v = p.split("=", 1)
                            k = k.lower().strip()
                            v = v.strip()
                            if k in ("voice", "veu", "id"):
                                spk_cfg.voice_id = v
                            elif k in ("pan", "panning"):
                                spk_cfg.pan = self.parse_pan(v)
                            elif k in ("speed", "rate", "velocitat"):
                                try:
                                    spk_cfg.speed = max(0.5, min(2.0, float(v)))
                                except ValueError:
                                    pass
                            elif k in ("pitch", "to"):
                                try:
                                    spk_cfg.pitch = max(-5.0, min(5.0, float(v)))
                                except ValueError:
                                    pass
                    continue

            # Dialogue processing
            d_match = dialogue_pattern.match(line)
            if d_match:
                mode = "DIALOGUE"
                spk_name = d_match.group(1).strip()
                speech_text = d_match.group(2).strip()

                if spk_name not in script.speakers:
                    v_id = default_voices[assigned_voice_idx % len(default_voices)]
                    p_val = default_pans[assigned_voice_idx % len(default_pans)]
                    
                    # If presenter / host, center panning
                    if any(term in spk_name.lower() for term in ("host", "presenter", "narrator", "presentadora")):
                        p_val = 0.0

                    assigned_voice_idx += 1
                    script.speakers[spk_name] = SpeakerConfig(
                        name=spk_name,
                        voice_id=v_id,
                        pan=p_val
                    )

                spk_cfg = script.speakers[spk_name]

                # Automatic conversational pause when switching speakers
                if last_speaker is not None and last_speaker != spk_name:
                    script.segments.append(PodcastSegment(
                        segment_type="pause",
                        pause_ms=script.turn_pause_ms,
                        raw_line="[AUTO_TURN_PAUSE]"
                    ))

                script.segments.append(PodcastSegment(
                    segment_type="dialogue",
                    speaker=spk_name,
                    text=speech_text,
                    pan=spk_cfg.pan,
                    speed=spk_cfg.speed,
                    pitch=spk_cfg.pitch,
                    voice_id=spk_cfg.voice_id,
                    raw_line=raw_line
                ))

                last_speaker = spk_name
            else:
                # Continuation line for the current speaker
                if mode == "DIALOGUE" and last_speaker and script.segments:
                    last_seg = script.segments[-1]
                    if last_seg.segment_type == "dialogue":
                        last_seg.text += " " + line
                        last_seg.raw_line += "\n" + raw_line

        return script
