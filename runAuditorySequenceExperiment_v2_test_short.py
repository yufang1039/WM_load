#!/usr/bin/env python
"""
Auditory Sequence Memory Experiment using PsychoPy
Tests temporal order memory for auditory syllable sequences

Converted from PsychToolbox MATLAB version
"""

import numpy as np
import os
import datetime
import json
import pandas as pd
import gc
from psychopy import visual, sound, core, event, data, gui, parallel
from psychopy.constants import STARTED, FINISHED
from psychopy import prefs

# prefs.hardware['audioLib'] = ['sounddevice', 'pyo', 'ptb']  # Try sounddevice first
# prefs.hardware['audioLatencyMode'] = 3
# prefs.hardware['sampleRate'] = 44100
# prefs.hardware["audioDevice"] == "Headphones (Realtek(R) Audio)"

class AuditorySequenceExperiment:
    def __init__(self):
        """Initialize the experiment with hyperparameters"""
        
        # HYPERPARAMETERS - Easily adjustable timing and experimental parameters
        self.params = {
            # Subject information
            'subject_id': '',                     # Subject ID (will be set via GUI)
            
            # EEG settings
            'use_eeg_triggers': True,            # Set to True to enable EEG triggers, False for local testing
            
            # Encoding phase timing (seconds)
            'encoding_fixation_duration': 0.6,    # Initial fixation duration
            'inter_syllable_interval': 0,       # Time between syllables
            
            # Retention phase timing (seconds)
            'retention_delay': 3.0,               # Delay after cue
            'neutral_impulse_duration': 0.1,      # White circle duration
            'post_impulse_fixation': 0.8,         # Fixation after impulse
            
            # Report phase timing (seconds)
            'report_response_time': 0.5,          # Time for report display
            'inter_report_interval': 0.2,         # Time between global and local rank reports
            'inter_trial_interval': 1.0,          # Empty screen duration between trials
            
            # Visual parameters
            'fixation_size': 1,                   # Fixation cross size (degrees)
            'circle_radius': 4.0,                 # Neutral impulse circle radius (degrees)
            'text_height': 0.8,                   # Text height (degrees)
            
            # Audio parameters
            'sample_rate': 44100,                 # Audio sample rate
            'audio_volume': 0.5,                  # Audio volume (0-1)
            
            # File paths
            'audio_base_path': 'chinese_audio_output',  # Base path for audio files
            'data_save_path': 'Data',                   # Base path for saving data
            
            # Block designs
            'block_designs': [
                {'name': 'three_3_syllable_words', 'num_words': 3, 'syllables_per_word': 3},
                {'name': 'three_4_syllable_words', 'num_words': 3, 'syllables_per_word': 4},
                {'name': 'four_3_syllable_words', 'num_words': 4, 'syllables_per_word': 3}
            ],
            
            # EEG trigger codes
            'trigger_cue_start': 1,
            'trigger_neutral_impulse': 2,
            'trigger_global_prompt': 3,
            'trigger_global_response': 4,
            'trigger_local_prompt': 5,
            'trigger_local_response': 6,
        }
        
        # Initialize components
        self.win = None
        self.fixation = None
        self.circle = None
        self.instruction_text = None
        self.response_text = None
        self.feedback_text = None
        self.results = []
        self.block_order = []
        self.paused = False
        
        # Try to initialize parallel port for EEG triggers only if enabled
        self.port = None
        self.eeg_enabled = False
        
        if self.params['use_eeg_triggers']:
            try:
                self.port = parallel.ParallelPort(address=0x7FF78)  # Adjust address as needed
                self.eeg_enabled = True
                print("EEG triggers enabled - parallel port initialized.")
            except:
                print("Warning: Could not initialize parallel port. EEG triggers disabled.")
                self.port = None
                self.eeg_enabled = False
        else:
            print("EEG triggers disabled (local testing mode).")
        
    def send_trigger(self, trigger_code):
        """Send EEG trigger"""
        if self.eeg_enabled and self.port:
            try:
                self.port.setData(trigger_code)
                core.wait(0.01)  # 10ms pulse
                self.port.setData(0)
            except Exception as e:
                print(f"Error sending trigger: {e}")
    
    def check_pause(self):
        """Check if user wants to pause/unpause"""
        keys = event.getKeys()
        if 'p' in keys:
            self.paused = not self.paused
            if self.paused:
                # Show pause message
                self.instruction_text.text = "PAUSED\n\nPress P to resume"
                self.instruction_text.draw()
                self.win.flip()
                
                # Wait for unpause
                while self.paused:
                    keys = event.waitKeys()
                    if 'p' in keys:
                        self.paused = False
                    elif 'escape' in keys:
                        core.quit()
        
        if 'escape' in keys:
            core.quit()
    
    def get_subject_info(self):
        """Get subject information via GUI dialog"""
        exp_info = {'Subject ID': ''}
        dlg = gui.DlgFromDict(dictionary=exp_info, title='Auditory Sequence Experiment')
        
        if dlg.OK:
            self.params['subject_id'] = exp_info['Subject ID']
            return True
        else:
            return False
        
    def setup_window(self):
        """Setup the display window"""
        self.win = visual.Window(
            size=[1024, 768],
            fullscr=True,  # Set to True for full screen
            screen=0,
            winType='pyglet',
            allowGUI=True,
            allowStencil=False,
            monitor='testMonitor',
            color=[0, 0, 0],
            colorSpace='rgb',
            blendMode='avg',
            useFBO=True,
            units='deg'
        )
        
    def setup_visual_components(self):
        """Setup visual components"""
        # Fixation cross
        self.fixation = visual.TextStim(
            win=self.win,
            text='+',
            height=self.params['fixation_size'],
            color='white',
            pos=(0, 0)
        )
        
        # Neutral impulse circle
        self.circle = visual.Circle(
            win=self.win,
            radius=self.params['circle_radius'],
            fillColor='white',
            lineColor='white',
            pos=(0, 0)
        )
        
        # Text stimuli
        self.instruction_text = visual.TextStim(
            win=self.win,
            height=self.params['text_height'],
            color='white',
            pos=(0, 0),
            wrapWidth=20
        )
        
        self.response_text = visual.TextStim(
            win=self.win,
            height=self.params['text_height'],
            color='white',
            pos=(0, 0),
            wrapWidth=20
        )
        
        self.feedback_text = visual.TextStim(
            win=self.win,
            height=self.params['text_height'],
            color='white',
            pos=(0, 0),
            wrapWidth=20
        )
    
    def generate_block_order(self):
        """Generate randomized block order for all designs"""
        # Collect all blocks organized by design
        blocks_by_design = {}
        
        for design in self.params['block_designs']:
            design_name = design['name']
            design_path = os.path.join(self.params['audio_base_path'], design_name)
            
            # Find all block directories
            if os.path.exists(design_path):
                block_dirs = [d for d in os.listdir(design_path) if d.startswith('block_') and os.path.isdir(os.path.join(design_path, d))]
                block_dirs.sort()
                
                blocks_by_design[design_name] = []
                for block_dir in block_dirs:
                    block_num = int(block_dir.split('_')[1])
                    blocks_by_design[design_name].append({
                        'design': design_name,
                        'block_num': block_num,
                        'num_words': design['num_words'],
                        'syllables_per_word': design['syllables_per_word']
                    })
        
        # Randomize blocks within each design
        for design_name in blocks_by_design:
            np.random.shuffle(blocks_by_design[design_name])
        
        # Create block order ensuring every 3 consecutive blocks contain all 3 designs
        all_blocks = []
        design_names = list(blocks_by_design.keys())
        
        # Determine how many complete triplets we can make
        min_blocks_per_design = min(len(blocks_by_design[d]) for d in design_names)
        
        # Create triplets (each triplet contains one block from each design)
        for i in range(min_blocks_per_design):
            # Create a triplet with one block from each design
            triplet = [blocks_by_design[d][i] for d in design_names]
            # Randomize order within the triplet
            np.random.shuffle(triplet)
            all_blocks.extend(triplet)
        
        # Add any remaining blocks (if designs have unequal numbers of blocks)
        for design_name in design_names:
            remaining_blocks = blocks_by_design[design_name][min_blocks_per_design:]
            all_blocks.extend(remaining_blocks)
        
        self.block_order = all_blocks
        
        # Create subject-specific data directory
        subject_dir = os.path.join(self.params['data_save_path'], self.params['subject_id'])
        os.makedirs(subject_dir, exist_ok=True)
        
        # Save block order to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(subject_dir, f"block_order_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.block_order, f, indent=2, ensure_ascii=False)
        
        print(f"Block order saved to {filename}")
        print(f"Total blocks: {len(self.block_order)}")
        
        return filename
    
    def get_trials_in_block(self, design_name, block_num):
        """Get list of trials in a block (limited to first 3 for testing)"""
        block_path = os.path.join(self.params['audio_base_path'], design_name, f'block_{block_num}')
        
        if not os.path.exists(block_path):
            print(f"Block path not found: {block_path}")
            return []
        
        trial_dirs = [d for d in os.listdir(block_path) if d.startswith('trial_') and os.path.isdir(os.path.join(block_path, d))]
        trial_dirs.sort(key=lambda x: int(x.split('_')[1]))
        
        # Only use first 3 trials for testing
        return trial_dirs[:3]
    
    def load_trial_audio(self, design_name, block_num, trial_dir, num_words, syllables_per_word):
        """Load audio file paths for a trial (just-in-time loading strategy)
        
        Returns filepaths instead of Sound objects to prevent memory buildup.
        Sound objects are created and destroyed immediately when needed during playback.
        """
        trial_path = os.path.join(self.params['audio_base_path'], design_name, f'block_{block_num}', trial_dir)
        words_path = os.path.join(trial_path, 'words')
        cue_path = os.path.join(trial_path, 'cue')
        
        # Load word syllables - store filepaths instead of Sound objects
        word_filepaths = []
        for word_idx in range(1, num_words + 1):
            syllable_filepaths = []
            for syl_idx in range(1, syllables_per_word + 1):
                # Find audio file matching pattern
                audio_files = [f for f in os.listdir(words_path) if f.startswith(f'word{word_idx}_syllable_{syl_idx}_')]
                
                if audio_files:
                    audio_file = audio_files[0]
                    audio_filepath = os.path.join(words_path, audio_file)
                    syllable_filepaths.append(audio_filepath)
                    print(f"Found: {audio_filepath}")
                else:
                    print(f"Audio file not found for word{word_idx}_syllable_{syl_idx}")
                    syllable_filepaths.append(None)
            
            word_filepaths.append(syllable_filepaths)
        
        # Load cue audio - store filepath
        cue_files = [f for f in os.listdir(cue_path) if f.endswith('.mp3')]
        cue_filepath = None
        cue_info = None
        
        if cue_files:
            cue_file = cue_files[0]
            cue_filepath = os.path.join(cue_path, cue_file)
            print(f"Found cue: {cue_filepath}")
            
            try:
                # Parse cue info from filename (e.g., word1_syllable_3_蒸馏水_水.mp3)
                parts = cue_file.split('_')
                cue_word = int(parts[0].replace('word', ''))
                cue_syllable = int(parts[2])
                cue_info = {'word': cue_word, 'syllable': cue_syllable}
            except Exception as e:
                print(f"Error parsing cue info from {cue_file}: {e}")
        
        return word_filepaths, cue_filepath, cue_info
    
    def show_instructions(self):
        """Show experiment instructions"""
        instructions = """Welcome to the Auditory Sequence Memory Experiment!

You will hear sequences of syllables from Chinese words.
After a delay, you will hear one syllable again as a cue.

Your task is to report TWO things:
1. GLOBAL position: Which word (1st, 2nd, 3rd, or 4th word)?
2. LOCAL position: Which syllable within that word?

Use number keys to respond.
Press P at any time to pause.
Press ESC to quit.

Each block starts with a practice trial.

Press any key to begin."""
        
        self.instruction_text.text = instructions
        self.instruction_text.draw()
        self.win.flip()
        event.waitKeys()
    
    def run_trial(self, trial_num, design_name, block_num, trial_dir, num_words, syllables_per_word, is_practice=False):
        """Run a single trial"""
        
        # Load audio filepaths for this trial
        word_filepaths, cue_filepath, cue_info = self.load_trial_audio(
            design_name, block_num, trial_dir, num_words, syllables_per_word
        )
        
        if not cue_filepath or not cue_info:
            print(f"Error: Could not load trial audio for {trial_dir}")
            return None
        
        print(f"Trial {trial_num}: {design_name}, Block {block_num}, {trial_dir}")
        
        # Randomly determine report order (True = global first, False = local first)
        global_first = bool(np.random.choice([True, False]))
        
        # ENCODING PHASE
        # Initial fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(self.params['encoding_fixation_duration'])
        self.check_pause()
        
        # Present all words and syllables in sequence
        for word_idx, syllable_filepaths in enumerate(word_filepaths):
            for syl_idx, syl_filepath in enumerate(syllable_filepaths):
                if syl_filepath:
                    # Show fixation during syllable
                    self.fixation.draw()
                    self.win.flip()
                    
                    # Load sound just-in-time
                    try:
                        syl_sound = sound.Sound(syl_filepath, sampleRate=48000)
                        
                        # Play syllable and wait for its duration
                        syl_sound.play()
                        core.wait(syl_sound.getDuration())
                        syl_sound.stop()
                        
                        # Immediately cleanup
                        del syl_sound
                        
                    except Exception as e:
                        print(f"Error playing {syl_filepath}: {e}")
                    
                    # Inter-syllable interval (except after last syllable of last word)
                    if not (word_idx == len(word_filepaths) - 1 and syl_idx == len(syllable_filepaths) - 1):
                        core.wait(self.params['inter_syllable_interval'])
                    
                    self.check_pause()
        
        # RETENTION PHASE
        print(f"Trial {trial_num}: Retention phase")
        
        # Present cue syllable - load just-in-time
        self.fixation.draw()
        self.win.flip()
        
        try:
            cue_sound = sound.Sound(cue_filepath, sampleRate=48000)
            
            self.send_trigger(self.params['trigger_cue_start'])
            cue_sound.play()
            core.wait(cue_sound.getDuration())
            cue_sound.stop()
            
            # Immediately cleanup
            del cue_sound
            
        except Exception as e:
            print(f"Error playing cue {cue_filepath}: {e}")
        
        # Retention delay
        core.wait(self.params['retention_delay'])
        self.check_pause()
        
        # Neutral impulse (white circle)
        self.send_trigger(self.params['trigger_neutral_impulse'])
        self.circle.draw()
        self.win.flip()
        core.wait(self.params['neutral_impulse_duration'])
        
        # Post-impulse fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(self.params['post_impulse_fixation'])
        self.check_pause()
        
        # REPORT PHASE
        print(f"Trial {trial_num}: Report phase (global_first={global_first})")
        
        # Initialize response variables
        global_response = None
        local_response = None
        global_rt = None
        local_rt = None
        
        # Define valid keys
        valid_global_keys = [str(i) for i in range(1, num_words + 1)]
        valid_local_keys = [str(i) for i in range(1, syllables_per_word + 1)]
        
        if global_first:
            # Report GLOBAL position first
            event.clearEvents(eventType='keyboard')
            
            global_prompt = f"Which WORD contained the cued syllable?\n\nPress 1"
            for i in range(2, num_words + 1):
                global_prompt += f", {i}"
            
            self.response_text.text = global_prompt
            self.response_text.draw()
            self.win.flip()
            self.send_trigger(self.params['trigger_global_prompt'])
            
            # Wait for global response
            timer = core.Clock()
            keys = event.waitKeys(keyList=valid_global_keys + ['p', 'escape'])
            
            if 'p' in keys:
                self.check_pause()
            
            if 'escape' in keys:
                core.quit()
            
            global_response = int(keys[0])
            global_rt = timer.getTime()
            self.send_trigger(self.params['trigger_global_response'])
            
            # Inter-report interval
            core.wait(self.params['inter_report_interval'])
            self.check_pause()
            
            # Report LOCAL position second
            event.clearEvents(eventType='keyboard')
            
            local_prompt = f"Which SYLLABLE within that word?\n\nPress 1"
            for i in range(2, syllables_per_word + 1):
                local_prompt += f", {i}"
            
            self.response_text.text = local_prompt
            self.response_text.draw()
            self.win.flip()
            self.send_trigger(self.params['trigger_local_prompt'])
            
            # Wait for local response
            timer = core.Clock()
            keys = event.waitKeys(keyList=valid_local_keys + ['p', 'escape'])
            
            if 'p' in keys:
                self.check_pause()
            
            if 'escape' in keys:
                core.quit()
            
            local_response = int(keys[0])
            local_rt = timer.getTime()
            self.send_trigger(self.params['trigger_local_response'])
            
        else:
            # Report LOCAL position first
            event.clearEvents(eventType='keyboard')
            
            local_prompt = f"Which SYLLABLE within the word?\n\nPress 1"
            for i in range(2, syllables_per_word + 1):
                local_prompt += f", {i}"
            
            self.response_text.text = local_prompt
            self.response_text.draw()
            self.win.flip()
            self.send_trigger(self.params['trigger_local_prompt'])
            
            # Wait for local response
            timer = core.Clock()
            keys = event.waitKeys(keyList=valid_local_keys + ['p', 'escape'])
            
            if 'p' in keys:
                self.check_pause()
            
            if 'escape' in keys:
                core.quit()
            
            local_response = int(keys[0])
            local_rt = timer.getTime()
            self.send_trigger(self.params['trigger_local_response'])
            
            # Inter-report interval
            core.wait(self.params['inter_report_interval'])
            self.check_pause()
            
            # Report GLOBAL position second
            event.clearEvents(eventType='keyboard')
            
            global_prompt = f"Which WORD contained the cued syllable?\n\nPress 1"
            for i in range(2, num_words + 1):
                global_prompt += f", {i}"
            
            self.response_text.text = global_prompt
            self.response_text.draw()
            self.win.flip()
            self.send_trigger(self.params['trigger_global_prompt'])
            
            # Wait for global response
            timer = core.Clock()
            keys = event.waitKeys(keyList=valid_global_keys + ['p', 'escape'])
            
            if 'p' in keys:
                self.check_pause()
            
            if 'escape' in keys:
                core.quit()
            
            global_response = int(keys[0])
            global_rt = timer.getTime()
            self.send_trigger(self.params['trigger_global_response'])
        
        # Brief display
        core.wait(self.params['report_response_time'])
        
        # Analyze responses
        correct_global = cue_info['word']
        correct_local = cue_info['syllable']
        
        global_correct = bool(global_response == correct_global)
        local_correct = bool(local_response == correct_local)
        both_correct = bool(global_correct and local_correct)
        
        # Show feedback for practice trials
        if is_practice:
            if both_correct:
                feedback_msg = f"Correct! Word {correct_global}, Syllable {correct_local}."
            else:
                feedback_msg = f"Incorrect.\nCorrect: Word {correct_global}, Syllable {correct_local}\n"
                feedback_msg += f"Your answer: Word {global_response}, Syllable {local_response}"
            
            self.feedback_text.text = feedback_msg
            self.feedback_text.draw()
            self.win.flip()
            core.wait(2.0)
        
        # Inter-trial interval - empty screen
        self.win.flip()
        core.wait(self.params['inter_trial_interval'])
        self.check_pause()
        
        # Prepare result
        result = {
            'subject_id': self.params['subject_id'],
            'trial': trial_num,
            'design': design_name,
            'block_num': block_num,
            'trial_dir': trial_dir,
            'num_words': num_words,
            'syllables_per_word': syllables_per_word,
            'correct_global': correct_global,
            'correct_local': correct_local,
            'global_response': global_response,
            'local_response': local_response,
            'global_correct': global_correct,
            'local_correct': local_correct,
            'both_correct': both_correct,
            'global_rt': global_rt,
            'local_rt': local_rt,
            'is_practice': is_practice,
            'global_first': global_first
        }
        
        print(f"Trial {trial_num} complete: Global {global_response} (correct: {correct_global}), Local {local_response} (correct: {correct_local})")
        
        # Force garbage collection and give audio subsystem time to fully release resources
        gc.collect()
        core.wait(0.05)  # Small delay to let audio backend cleanup
        
        return result
    
    def run_experiment(self):
        """Run the complete experiment"""
        try:
            # Get subject information
            if not self.get_subject_info():
                print("Experiment cancelled by user.")
                return
            
            # Setup
            self.setup_window()
            self.setup_visual_components()
            
            # Generate and save block order
            block_order_file = self.generate_block_order()
            
            # Show instructions
            self.show_instructions()
            
            # Run all blocks
            print("Starting experiment...")
            self.results = []
            trial_counter = 0
            
            for block_idx, block_info in enumerate(self.block_order, 1):
                design_name = block_info['design']
                block_num = block_info['block_num']
                num_words = block_info['num_words']
                syllables_per_word = block_info['syllables_per_word']
                
                # Get trials in this block (limited to first 3 for testing)
                trial_dirs = self.get_trials_in_block(design_name, block_num)
                
                if not trial_dirs:
                    print(f"No trials found for {design_name}, block {block_num}")
                    continue
                
                # Show block start message
                block_msg = f"Block {block_idx} of {len(self.block_order)}\n\n"
                block_msg += f"{design_name.replace('_', ' ').title()}\n\n"
                block_msg += f"First trial is practice.\n\n"
                block_msg += "Press any key to start."
                
                self.instruction_text.text = block_msg
                self.instruction_text.draw()
                self.win.flip()
                event.waitKeys()
                
                # Run trials in block
                for trial_idx, trial_dir in enumerate(trial_dirs):
                    self.check_pause()
                    
                    trial_counter += 1
                    is_practice = (trial_idx == 0)  # First trial is practice
                    
                    result = self.run_trial(
                        trial_counter,
                        design_name,
                        block_num,
                        trial_dir,
                        num_words,
                        syllables_per_word,
                        is_practice=is_practice
                    )
                    
                    if result:
                        self.results.append(result)
                
                # Save results after each block
                self.save_results()
                print(f"Results saved after block {block_idx}")
                
                # Block complete message
                if block_idx < len(self.block_order):
                    block_complete_msg = f"Block {block_idx} complete!\n\nTake a short break.\n\nPress any key to continue."
                    self.instruction_text.text = block_complete_msg
                    self.instruction_text.draw()
                    self.win.flip()
                    event.waitKeys()
            
            # Show final results
            if self.results:
                # Filter out practice trials for final stats
                main_results = [r for r in self.results if not r['is_practice']]
                
                if main_results:
                    global_correct = [r for r in main_results if r['global_correct']]
                    local_correct = [r for r in main_results if r['local_correct']]
                    both_correct = [r for r in main_results if r['both_correct']]
                    
                    global_acc = len(global_correct) / len(main_results) * 100
                    local_acc = len(local_correct) / len(main_results) * 100
                    both_acc = len(both_correct) / len(main_results) * 100
                    
                    valid_global_rts = [r['global_rt'] for r in main_results if r['global_rt'] is not None]
                    valid_local_rts = [r['local_rt'] for r in main_results if r['local_rt'] is not None]
                    
                    avg_global_rt = np.mean(valid_global_rts) if valid_global_rts else 0
                    avg_local_rt = np.mean(valid_local_rts) if valid_local_rts else 0
                    
                    results_text = f"""Experiment Complete!

Global Position Accuracy: {global_acc:.1f}%
Local Position Accuracy: {local_acc:.1f}%
Both Correct: {both_acc:.1f}%

Average Global RT: {avg_global_rt:.2f}s
Average Local RT: {avg_local_rt:.2f}s

Press any key to exit."""
                    
                    self.instruction_text.text = results_text
                    self.instruction_text.draw()
                    self.win.flip()
                    event.waitKeys()
                
                # Save results
                self.save_results()
            
        except Exception as e:
            print(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.cleanup()
    
    def save_results(self):
        """Save experimental results"""
        # Create subject-specific data directory
        subject_dir = os.path.join(self.params['data_save_path'], self.params['subject_id'])
        os.makedirs(subject_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(subject_dir, f"auditory_sequence_results_{timestamp}.json")
        
        data_to_save = {
            'results': self.results,
            'params': self.params,
            'block_order': self.block_order,
            'timestamp': timestamp
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {filename}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.win:
            self.win.close()
        core.quit()


def main():
    """Main function to run the experiment"""
    experiment = AuditorySequenceExperiment()
    experiment.run_experiment()


if __name__ == "__main__":
    main()