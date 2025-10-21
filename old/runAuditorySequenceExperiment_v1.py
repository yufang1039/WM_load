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
from psychopy import visual, sound, core, event, data, gui
from psychopy.constants import STARTED, FINISHED


class AuditorySequenceExperiment:
    def __init__(self):
        """Initialize the experiment with hyperparameters"""
        
        # HYPERPARAMETERS - Easily adjustable timing and experimental parameters
        self.params = {
            # Encoding phase timing (seconds)
            'encoding_fixation_duration': 0.6,    # Initial fixation duration
            'syllable_duration': 1.6,             # Duration for each syllable presentation
            'inter_syllable_interval': 2.0,       # Time between syllables
            'num_syllables': 4,                   # Number of syllables in sequence
            
            # Retention phase timing (seconds)
            'cue_syllable_duration': 0.2,         # Duration of cue syllable
            'retention_delay': 3.0,               # Delay after cue
            'neutral_impulse_duration': 0.1,      # White circle duration
            'post_impulse_fixation': 0.8,         # Fixation after impulse
            
            # Report phase timing (seconds)
            'report_response_time': 0.2,          # Time for report display
            'max_response_time': 5.0,             # Maximum time to wait for response
            
            # Visual parameters
            'fixation_size': 0.5,                 # Fixation cross size (degrees)
            'circle_radius': 4.0,                 # Neutral impulse circle radius (degrees)
            'text_height': 0.8,                   # Text height (degrees)
            
            # Audio parameters
            'sample_rate': 44100,                 # Audio sample rate
            'audio_volume': 0.5,                  # Audio volume (0-1)
            
            # Experiment parameters
            'num_trials': 20,                     # Number of experimental trials
            'practice_trials': 3,                 # Number of practice trials
        }
        
        # Initialize components
        self.win = None
        self.fixation = None
        self.circle = None
        self.instruction_text = None
        self.response_text = None
        self.feedback_text = None
        self.syllables = []
        self.results = []
        
    def setup_window(self):
        """Setup the display window"""
        self.win = visual.Window(
            size=[1024, 768],
            fullscr=False,  # Set to True for full screen
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
        
    def create_syllable_sounds(self):
        """Create synthetic syllable sounds"""
        duration = self.params['syllable_duration']
        sample_rate = self.params['sample_rate']
        
        # Create 8 different synthetic syllables with different frequency patterns
        frequencies = [440, 523, 659, 784, 880, 1047, 1319, 1568]  # Musical notes
        
        self.syllables = []
        
        for i, freq in enumerate(frequencies):
            # Create time vector
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Create a simple tone
            tone = np.sin(2 * np.pi * freq * t)
            
            # Apply envelope to avoid clicks
            envelope_length = int(0.05 * sample_rate)  # 50ms envelope
            envelope = np.ones_like(tone)
            
            if len(tone) > 2 * envelope_length:
                envelope[:envelope_length] = np.linspace(0, 1, envelope_length)
                envelope[-envelope_length:] = np.linspace(1, 0, envelope_length)
            
            syllable = tone * envelope * self.params['audio_volume']
            
            # Create PsychoPy sound object
            sound_obj = sound.Sound(
                value=syllable,
                sampleRate=sample_rate,
                loops=0
            )
            self.syllables.append(sound_obj)
    
    def show_instructions(self):
        """Show experiment instructions"""
        instructions = """Welcome to the Auditory Sequence Memory Experiment!

You will hear a sequence of 4 different syllables.
After a delay, you will hear one of these syllables again as a cue.
Your task is to report the temporal position (1st, 2nd, 3rd, or 4th)
of the cued syllable in the original sequence.

Press keys 1, 2, 3, or 4 to respond.
You can press ESC at any time to quit the experiment.

We will start with a few practice trials.

Press any key to begin."""
        
        self.instruction_text.text = instructions
        self.instruction_text.draw()
        self.win.flip()
        event.waitKeys()
        
    def run_trial(self, trial_num, is_practice=False):
        """Run a single trial of the experiment"""
        
        # Select syllables for this trial (random order)
        syllable_indices = np.random.choice(len(self.syllables), self.params['num_syllables'], replace=False)
        
        print(f"Trial {trial_num}: Encoding phase")
        
        # ENCODING PHASE
        # Initial fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(self.params['encoding_fixation_duration'])
        
        # Present syllable sequence
        for i in range(self.params['num_syllables']):
            syllable_idx = syllable_indices[i]
            
            # Show fixation during syllable
            self.fixation.draw()
            self.win.flip()
            
            # Play syllable
            self.syllables[syllable_idx].play()
            core.wait(self.params['syllable_duration'])
            self.syllables[syllable_idx].stop()
            
            # Inter-syllable interval (except after last syllable)
            if i < self.params['num_syllables'] - 1:
                core.wait(self.params['inter_syllable_interval'])
        
        # RETENTION PHASE
        print(f"Trial {trial_num}: Retention phase")
        
        # Select random syllable to cue (0-3, will be reported as 1-4)
        cued_position = np.random.randint(self.params['num_syllables'])
        cued_syllable_idx = syllable_indices[cued_position]
        
        # Present cue syllable
        self.fixation.draw()
        self.win.flip()
        
        self.syllables[cued_syllable_idx].play()
        core.wait(self.params['cue_syllable_duration'])
        self.syllables[cued_syllable_idx].stop()
        
        # Retention delay
        core.wait(self.params['retention_delay'])
        
        # Neutral impulse (white circle)
        self.circle.draw()
        self.win.flip()
        core.wait(self.params['neutral_impulse_duration'])
        
        # Post-impulse fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(self.params['post_impulse_fixation'])
        
        # REPORT PHASE
        print(f"Trial {trial_num}: Report phase")
        
        # Clear any previous key presses before showing response prompt
        event.clearEvents(eventType='keyboard')
        
        # Show response options
        response_prompt = "What was the temporal position of the cued syllable?\n\nPress 1, 2, 3, or 4"
        self.response_text.text = response_prompt
        self.response_text.draw()
        self.win.flip()
        
        # Wait for response - only accept keys after prompt is displayed
        timer = core.Clock()
        response = None
        reaction_time = None
        
        valid_keys = ['1', '2', '3', '4']
        
        while timer.getTime() < self.params['max_response_time']:
            keys = event.getKeys(keyList=valid_keys + ['escape'])
            
            if keys:
                if 'escape' in keys:
                    print("Experiment terminated by user.")
                    self.cleanup()
                    core.quit()
                
                key = keys[0]
                if key in valid_keys:
                    response = int(key)
                    reaction_time = timer.getTime()
                    break
        
        # Brief display of response time
        core.wait(self.params['report_response_time'])
        
        # Analyze response
        correct_position = cued_position + 1  # Convert to 1-4 scale
        correct = (response == correct_position) if response is not None else False
        
        # Show feedback for practice trials
        if is_practice:
            if response is None:
                feedback_msg = "Too slow! Please respond faster."
            elif correct:
                feedback_msg = f"Correct! The cued syllable was in position {correct_position}."
            else:
                feedback_msg = f"Incorrect. The cued syllable was in position {correct_position}, you answered {response}."
            
            self.feedback_text.text = feedback_msg
            self.feedback_text.draw()
            self.win.flip()
            core.wait(2.0)
        
        # Prepare result
        result = {
            'trial': trial_num,
            'cued_position': correct_position,
            'response': response,
            'correct': correct,
            'reaction_time': reaction_time
        }
        
        print(f"Trial {trial_num} complete: Position {correct_position}, Response {response}, Correct: {correct}")
        
        return result
    
    def run_experiment(self):
        """Run the complete experiment"""
        try:
            # Setup
            self.setup_window()
            self.setup_visual_components()
            self.create_syllable_sounds()
            
            # Show instructions
            self.show_instructions()
            
            # Run practice trials
            print("Starting practice trials...")
            for trial in range(1, self.params['practice_trials'] + 1):
                # Check for escape
                if event.getKeys(keyList=['escape']):
                    print("Experiment terminated by user.")
                    return
                
                self.run_trial(trial, is_practice=True)
            
            # Transition to main experiment
            transition_text = "Practice complete!\n\nPress any key to start the main experiment."
            self.instruction_text.text = transition_text
            self.instruction_text.draw()
            self.win.flip()
            event.waitKeys()
            
            # Run main experiment
            print("Starting main experiment...")
            self.results = []
            
            for trial in range(1, self.params['num_trials'] + 1):
                # Check for escape
                if event.getKeys(keyList=['escape']):
                    print("Experiment terminated by user.")
                    break
                
                result = self.run_trial(trial, is_practice=False)
                self.results.append(result)
            
            # Show results
            if self.results:
                correct_trials = [r for r in self.results if r['correct']]
                accuracy = len(correct_trials) / len(self.results) * 100
                
                valid_rts = [r['reaction_time'] for r in self.results if r['reaction_time'] is not None]
                avg_rt = np.mean(valid_rts) if valid_rts else 0
                
                results_text = f"""Experiment Complete!

Accuracy: {accuracy:.1f}%
Average Response Time: {avg_rt:.2f} seconds

Press any key to exit."""
                
                self.instruction_text.text = results_text
                self.instruction_text.draw()
                self.win.flip()
                event.waitKeys()
                
                # Save results
                self.save_results()
            
        except Exception as e:
            print(f"Error occurred: {e}")
            raise
        finally:
            self.cleanup()
    
    def save_results(self):
        """Save experimental results"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auditory_sequence_results_{timestamp}.json"
        
        data_to_save = {
            'results': self.results,
            'params': self.params,
            'timestamp': timestamp
        }
        
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
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