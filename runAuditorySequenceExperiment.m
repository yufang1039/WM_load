function runAuditorySequenceExperiment()
    % Auditory Sequence Memory Experiment using PsychToolbox
    % Tests temporal order memory for auditory syllable sequences
    
    %% HYPERPARAMETERS - Easily adjustable timing and experimental parameters
    params = struct();
    
    % Encoding phase timing (ms)
    params.encoding_fixation_duration = 600;    % Initial fixation duration
    params.syllable_duration = 1600;            % Duration for each syllable presentation
    params.inter_syllable_interval = 2000;      % Time between syllables
    params.num_syllables = 4;                   % Number of syllables in sequence
    
    % Retention phase timing (ms)
    params.cue_syllable_duration = 200;         % Duration of cue syllable
    params.retention_delay = 3000;              % Delay after cue
    params.neutral_impulse_duration = 100;      % White circle duration
    params.post_impulse_fixation = 800;         % Fixation after impulse
    
    % Report phase timing (ms)
    params.report_response_time = 200;          % Time for report display
    params.max_response_time = 5000;            % Maximum time to wait for response
    
    % Visual parameters
    params.fixation_size = 20;                  % Fixation cross size (pixels)
    params.circle_radius = 50;                  % Neutral impulse circle radius
    params.text_size = 24;                      % Text size for instructions
    
    % Audio parameters
    params.sample_rate = 44100;                 % Audio sample rate
    params.audio_volume = 0.5;                  % Audio volume (0-1)
    
    % Experiment parameters
    params.num_trials = 20;                     % Number of experimental trials
    params.practice_trials = 3;                 % Number of practice trials
    
    %% Initialize PsychToolbox
    try
        % Initialize PTB with unified key names
        KbName('UnifyKeyNames');
        
        % Get screen info
        screens = Screen('Screens');
        screenNumber = max(screens);
        
        % Open window
        [window, windowRect] = PsychImaging('OpenWindow', screenNumber, [128 128 128]);
        [screenXpixels, screenYpixels] = Screen('WindowSize', window);
        [xCenter, yCenter] = RectCenter(windowRect);
        
        % Initialize audio
        InitializePsychSound(1);
        pahandle = PsychPortAudio('Open', [], 1, 1, params.sample_rate, 2);
        
        % Set text properties
        Screen('TextSize', window, params.text_size);
        Screen('TextFont', window, 'Arial');
        
        % Define colors
        white = [255 255 255];
        black = [0 0 0];
        gray = [128 128 128];
        
        %% Create syllable sounds
        syllables = createSyllableSounds(params);
        
        %% Show instructions
        showInstructions(window, xCenter, yCenter, white);
        
        %% Run practice trials
        fprintf('Starting practice trials...\n');
        for trial = 1:params.practice_trials
            runTrial(window, pahandle, syllables, params, trial, true, ...
                    xCenter, yCenter, white, black, gray);
        end
        
        % Show transition to main experiment
        DrawFormattedText(window, 'Practice complete!\n\nPress any key to start the main experiment.', ...
                         'center', 'center', white);
        Screen('Flip', window);
        KbStrokeWait;
        
        %% Run main experiment
        fprintf('Starting main experiment...\n');
        results = struct('trial', {}, 'cued_position', {}, 'response', {}, ...
                        'correct', {}, 'reaction_time', {});

        escapeKey = KbName('ESCAPE');
        
        for trial = 1:params.num_trials

            % Check for escape key
            [keyIsDown, ~, keyCode] = KbCheck;
            if keyIsDown
                if keyCode(escapeKey)
                    % Display 'Thank you for your time' message
                    DrawFormattedText(window, 'Thank you for your time', 'center', 'center', [255 255 255]);
                    Screen('Flip', window);
                    
                    % Wait a second for the participant to read the message
                    WaitSecs(1);
                    
                    % Break out of the loop, ending the experiment
                    break;
                end
            end
            
            result = runTrial(window, pahandle, syllables, params, trial, false, ...
                             xCenter, yCenter, white, black, gray);
            results(trial) = result;
        end
        
        %% Show results
        accuracy = mean([results.correct]);
        avg_rt = mean([results.reaction_time]);
        
        resultsText = sprintf('Experiment Complete!\n\nAccuracy: %.1f%%\nAverage Response Time: %.2f seconds\n\nPress any key to exit.', ...
                             accuracy * 100, avg_rt);
        DrawFormattedText(window, resultsText, 'center', 'center', white);
        Screen('Flip', window);
        KbStrokeWait;
        
        %% Save results
        save(sprintf('auditory_sequence_results_%s.mat', datestr(now, 'yyyymmdd_HHMMSS')), ...
             'results', 'params');
        
    catch ME
        % Clean up on error
        fprintf('Error occurred: %s\n', ME.message);
        sca;
        PsychPortAudio('Close');
        rethrow(ME);
    end
    
    %% Clean up
    sca;
    PsychPortAudio('Close');
    fprintf('Experiment completed successfully!\n');
end

function result = runTrial(window, pahandle, syllables, params, trialNum, isPractice, ...
                          xCenter, yCenter, white, black, gray)
    % Run a single trial of the experiment
    
    % Select syllables for this trial (random order)
    syllable_order = randperm(length(syllables), params.num_syllables);
    
    %% ENCODING PHASE
    fprintf('Trial %d: Encoding phase\n', trialNum);
    
    % Initial fixation
    drawFixation(window, xCenter, yCenter, params.fixation_size, white);
    Screen('Flip', window);
    WaitSecs(params.encoding_fixation_duration / 1000);
    
    % Present syllable sequence
    for i = 1:params.num_syllables
        % Play syllable
        syllable_idx = syllable_order(i);
        PsychPortAudio('FillBuffer', pahandle, syllables{syllable_idx});
        
        % Show fixation during syllable
        drawFixation(window, xCenter, yCenter, params.fixation_size, white);
        Screen('Flip', window);
        
        % Start audio and wait
        PsychPortAudio('Start', pahandle, 1, 0, 1);
        WaitSecs(params.syllable_duration / 1000);
        PsychPortAudio('Stop', pahandle, 1);
        
        % Inter-syllable interval (except after last syllable)
        if i < params.num_syllables
            WaitSecs(params.inter_syllable_interval / 1000);
        end
    end
    
    %% RETENTION PHASE
    fprintf('Trial %d: Retention phase\n', trialNum);
    
    % Select random syllable to cue (1-4)
    cued_position = randi(params.num_syllables);
    cued_syllable_idx = syllable_order(cued_position);
    
    % Present cue syllable
    PsychPortAudio('FillBuffer', pahandle, syllables{cued_syllable_idx});
    drawFixation(window, xCenter, yCenter, params.fixation_size, white);
    Screen('Flip', window);
    
    PsychPortAudio('Start', pahandle, 1, 0, 1);
    WaitSecs(params.cue_syllable_duration / 1000);
    PsychPortAudio('Stop', pahandle, 1);
    
    % Retention delay
    WaitSecs(params.retention_delay / 1000);
    
    % Neutral impulse (white circle)
    Screen('FillOval', window, white, ...
           [xCenter - params.circle_radius, yCenter - params.circle_radius, ...
            xCenter + params.circle_radius, yCenter + params.circle_radius]);
    Screen('Flip', window);
    WaitSecs(params.neutral_impulse_duration / 1000);
    
    % Post-impulse fixation
    drawFixation(window, xCenter, yCenter, params.fixation_size, white);
    Screen('Flip', window);
    WaitSecs(params.post_impulse_fixation / 1000);
    
    %% REPORT PHASE
    fprintf('Trial %d: Report phase\n', trialNum);
    
    % Show response options
    responseText = 'What was the temporal position of the cued syllable?\n\nPress 1, 2, 3, or 4';
    DrawFormattedText(window, responseText, 'center', 'center', white);
    Screen('Flip', window);
    
    % Wait for response
    startTime = GetSecs;
    validKeys = {'1!', '2@', '3#', '4$'};  % Key codes for 1-4
    
    while true
        [keyIsDown, secs, keyCode] = KbCheck;
        if keyIsDown
            keyName = KbName(keyCode);
            if ismember(keyName, validKeys)
                response = str2double(keyName(1));
                reaction_time = secs - startTime;
                break;
            elseif strcmp(keyName, 'ESCAPE')
                fprintf('Experiment terminated by user.\n');
                sca;
                PsychPortAudio('Close');
                return;
            end
        end
        
        % Timeout check
        if GetSecs - startTime > params.max_response_time / 1000
            response = NaN;
            reaction_time = NaN;
            break;
        end
    end
    
    % Brief display of response time
    WaitSecs(params.report_response_time / 1000);
    
    %% Analyze response
    correct = (response == cued_position);
    
    % Show feedback for practice trials
    if isPractice
        if isnan(response)
            feedbackText = 'Too slow! Please respond faster.';
        elseif correct
            feedbackText = sprintf('Correct! The cued syllable was in position %d.', cued_position);
        else
            feedbackText = sprintf('Incorrect. The cued syllable was in position %d, you answered %d.', ...
                                  cued_position, response);
        end
        
        DrawFormattedText(window, feedbackText, 'center', 'center', white);
        Screen('Flip', window);
        WaitSecs(2);
    end
    
    % Prepare result structure
    result = struct('trial', trialNum, 'cued_position', cued_position, ...
                   'response', response, 'correct', correct, ...
                   'reaction_time', reaction_time);
    
    fprintf('Trial %d complete: Position %d, Response %d, Correct: %d\n', ...
            trialNum, cued_position, response, correct);
end

function syllables = createSyllableSounds(params)
    % Create synthetic syllable sounds
    % In a real experiment, you would load actual syllable recordings
    
    duration = params.syllable_duration / 1000;  % Convert to seconds
    t = 0:1/params.sample_rate:duration-1/params.sample_rate;  % Fixed time vector
    
    % Create 8 different synthetic syllables with different frequency patterns
    frequencies = [440, 523, 659, 784, 880, 1047, 1319, 1568];  % Musical notes
    
    syllables = cell(length(frequencies), 1);
    
    for i = 1:length(frequencies)
        % Create a simple tone with envelope
        tone = sin(2 * pi * frequencies(i) * t);
        
        % Apply envelope to avoid clicks
        envelope_length = round(0.05 * params.sample_rate);  % 50ms envelope
        envelope = ones(size(tone));
        if length(tone) > 2 * envelope_length
            envelope(1:envelope_length) = linspace(0, 1, envelope_length);
            envelope(end-envelope_length+1:end) = linspace(1, 0, envelope_length);
        end
        
        syllable = tone .* envelope * params.audio_volume;
        
        % Make stereo (2 channels x N samples)
        syllables{i} = [syllable; syllable];
    end
end

function drawFixation(window, xCenter, yCenter, size, color)
    % Draw a fixation cross
    Screen('DrawLine', window, color, xCenter - size/2, yCenter, xCenter + size/2, yCenter, 3);
    Screen('DrawLine', window, color, xCenter, yCenter - size/2, xCenter, yCenter + size/2, 3);
end

function showInstructions(window, xCenter, yCenter, color)
    % Show experiment instructions
    instructions = ['Welcome to the Auditory Sequence Memory Experiment!\n\n' ...
                   'You will hear a sequence of 4 different syllables.\n' ...
                   'After a delay, you will hear one of these syllables again as a cue.\n' ...
                   'Your task is to report the temporal position (1st, 2nd, 3rd, or 4th)\n' ...
                   'of the cued syllable in the original sequence.\n\n' ...
                   'Press keys 1, 2, 3, or 4 to respond.\n' ...
                   'You can press ESC at any time to quit the experiment.\n\n' ...
                   'We will start with a few practice trials.\n\n' ...
                   'Press any key to begin.'];
    
    DrawFormattedText(window, instructions, 'center', 'center', color);
    Screen('Flip', window);
    KbStrokeWait;
end