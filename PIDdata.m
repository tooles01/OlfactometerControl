%% ST 2020
% PIDdata.m

%%
%#ok<*SAGROW>
clear variables
%close all

%% Load data
%file = '2020-10-14_mainDatafile_01.csv';
file = '2020-10-19_exp01_12.csv';

data_wholeFile = readcell(file);
headerGoesTil = (find(strcmp(data_wholeFile,'Time')))+1;
rawData = data_wholeFile(headerGoesTil:end,:);
numData = size(rawData);
numData = numData(1);

%% Get time (convert to s)
rawTime = rawData(:,1);
rawTime = vertcat(rawTime{:});
rawTime = rawTime-rawTime(1);
rawTime = milliseconds(rawTime);
rawTime = rawTime/1000;

% Get rest of data
rawInst = rawData(:,2);
rawPara = rawData(:,3);
rawVals = rawData(:,4);

%% Parse by instrument
e=1;
a_1=1; a_2=1; b_1=1; b_2=1;
p=1;
event_data = {};
olfa_dataA1 = {1,1};
olfa_dataA2 = {1,1};
olfa_dataB1 = {1,1};
olfa_dataB2 = {1,1};
for i=1:numData
    i_time = rawTime(i);
    i_inst = rawInst{i};
    i_para = rawPara{i};
    i_valu = rawVals{i};
    if strcmp(i_para,'OV') == 1
        event_data{e,1} = i_time;
        event_data{e,2} = i_inst;
        event_data{e,3} = i_para;
        event_data{e,4} = i_valu;
        e=e+1;
        event_data{e,1} = i_time + i_valu;
        event_data{e,2} = i_inst;
        event_data{e,3} = 'CV';
        e=e+1;
    else
        if strcmp(i_inst,'olfa prototype A1') == 1
            olfa_dataA1{a_1,1} = i_time;
            olfa_dataA1{a_1,2} = i_valu;
            a_1=a_1+1;
        elseif strcmp(i_inst,'olfa prototype A2') == 1
            olfa_dataA2{a_2,1} = i_time;
            olfa_dataA2{a_2,2} = i_valu;
            a_2=a_2+1;
        elseif strcmp(i_inst,'olfa prototype B1') == 1
            olfa_dataB1{b_1,1} = i_time;
            olfa_dataB1{b_1,2} = i_valu;
            b_1=b_1+1;
        elseif strcmp(i_inst,'olfa prototype B2') == 1
            olfa_dataB2{b_2,1} = i_time;
            olfa_dataB2{b_2,2} = i_valu;
            b_2=b_2+1;
        elseif strcmp(i_inst,'PID reading') == 1
            pid_data{p,1} = i_time;
            pid_data{p,2} = i_valu;
            p=p+1;
        end
    end
end
olfaA1 = cell2mat(olfa_dataA1);
olfaA2 = cell2mat(olfa_dataA2);
olfaB1 = cell2mat(olfa_dataB1);
olfaB2 = cell2mat(olfa_dataB2);
pid = cell2mat(pid_data);

%% convert olfa data to sccm
load('Honeywell3100V.mat');
A1_sccm = intToSCCM(olfaA1,Honeywell3100V);
A2_sccm = intToSCCM(olfaA2,Honeywell3100V);
B1_sccm = intToSCCM(olfaB1,Honeywell3100V);
B2_sccm = intToSCCM(olfaB2,Honeywell3100V);


%% Plot olfa data
pos = [50 100 1850 875];
f1 = figure('Position',pos,'Name',file,'NumberTitle','off'); hold on;
legend('Location','northeast');
title(file)

xlabel('Time (s)');
ylabel('Flow (SCCM)');
ax = gca;
xmin = min(pid(:,1));
xmax = max(pid(:,1));
ax.XLim = [xmin xmax];
ax.YLim = [-10 110];
plot(A1_sccm(:,1),A1_sccm(:,2),'DisplayName','A1 flow');
plot(A2_sccm(:,1),A2_sccm(:,2),'DisplayName','A2 flow');
plot(B1_sccm(:,1),B1_sccm(:,2),'DisplayName','B1 flow');
plot(B2_sccm(:,1),B2_sccm(:,2),'DisplayName','B2 flow');

%% Plot PID data
pid(:,2) = pid(:,2) * 1000;   % convert V to mV
ymin = min(pid(:,2)) - 250;
ymax = max(pid(:,2)) + 250;

yyaxis right;
ylabel('PID value (mV)');
%ax.YLim = [ymin ymax];
ax.YLim = [-3000 1000];
plot(pid(:,1),pid(:,2),'DisplayName','PID data','LineWidth',2);
hold off;


%% Split into sections
%{
eventSec = struct([]);
numEvents = size(event_data); numSections = numEvents(1)*2;
endOfLast = 0;
e=1;
% this only works if there are no overlapping events
for i=1:numEvents
    eventStart = event_data{i,1};
    %eventDur = event_data{i,4};
    %eventEnd = eventStart + eventDur;
    
    %% EVENT 1
    % preEvent: end of last until event start
    startTime = endOfLast;
    endTime = eventStart;
    if (endTime-startTime) > 0 
    %if (endTime-startTime) ~= 0
        i_sA1 = find(A1_sccm(:,1)>startTime,1,'first');
        i_eA1 = find(A1_sccm(:,1)>endTime,1,'first');
        A1_sec = A1_sccm((i_sA1:i_eA1-1),:);
        A1_avg = mean(A1_sec(:,2));
        i_sA2 = find(A2_sccm(:,1)>startTime,1,'first');
        i_eA2 = find(A2_sccm(:,1)>endTime,1,'first');
        A2_sec = A2_sccm((i_sA2:i_eA2-1),:);
        A2_avg = mean(A2_sec(:,2));
        i_sB1 = find(B1_sccm(:,1)>startTime,1,'first');
        i_eB1 = find(B1_sccm(:,1)>endTime,1,'first');
        B1_sec = B1_sccm((i_sB1:i_eB1-1),:);
        B1_avg = mean(B1_sec(:,2));
        i_sB2 = find(B2_sccm(:,1)>startTime,1,'first');
        i_eB2 = find(B2_sccm(:,1)>endTime,1,'first');
        B2_sec = B2_sccm((i_sB2:i_eB2-1),:);
        B2_avg = mean(B2_sec(:,2));
        i_sPID = find(pid(:,1)>startTime,1,'first');
        i_ePID = find(pid(:,1)>endTime,1,'first');
        PID_sec = pid((i_sPID:i_ePID-1),:);
        PID_avg = mean(PID_sec(:,2));

        eventSec(e).event = e;
        eventSec(e).startTime = startTime;
        eventSec(e).endTime = endTime;
        eventSec(e).PIDavg = PID_avg;
        eventSec(e).A1avg = A1_avg;
        eventSec(e).A2avg = A2_avg;
        eventSec(e).B1avg = B1_avg;
        eventSec(e).B2avg = B2_avg;
        eventSec(e).PIDdata = PID_sec;
        eventSec(e).A1data = A1_sec;
        eventSec(e).A2data = A2_sec;
        eventSec(e).B1data = B1_sec;
        eventSec(e).B2data = B2_sec;
        e=e+1;
        endOfLast = endTime;
    end
    %% EVENT 2
    % during actual event
    if (i+1) < numEvents
        startTime = eventStart;
        endTime = event_data{i+1,1};
        i_sA1 = find(A1_sccm(:,1)>startTime,1,'first');
        i_eA1 = find(A1_sccm(:,1)>endTime,1,'first');
        A1_sec = A1_sccm((i_sA1:i_eA1-1),:);
        A1_avg = mean(A1_sec(:,2));
        i_sA2 = find(A2_sccm(:,1)>startTime,1,'first');
        i_eA2 = find(A2_sccm(:,1)>endTime,1,'first');
        A2_sec = A2_sccm((i_sA2:i_eA2-1),:);
        A2_avg = mean(A2_sec(:,2));
        i_sB1 = find(B1_sccm(:,1)>startTime,1,'first');
        i_eB1 = find(B1_sccm(:,1)>endTime,1,'first');
        B1_sec = B1_sccm((i_sB1:i_eB1-1),:);
        B1_avg = mean(B1_sec(:,2));
        i_sB2 = find(B2_sccm(:,1)>startTime,1,'first');
        i_eB2 = find(B2_sccm(:,1)>endTime,1,'first');
        B2_sec = B2_sccm((i_sB2:i_eB2-1),:);
        B2_avg = mean(B2_sec(:,2));
        i_sPID = find(pid(:,1)>startTime,1,'first');
        i_ePID = find(pid(:,1)>endTime,1,'first');
        PID_sec = pid((i_sPID:i_ePID-1),:);
        PID_avg = mean(PID_sec(:,2));

        eventSec(e).event = e;
        eventSec(e).startTime = startTime;
        eventSec(e).endTime = endTime;
        eventSec(e).PIDdata = PID_sec;
        eventSec(e).PIDavg = PID_avg;
        eventSec(e).A1data = A1_sec;
        eventSec(e).A1avg = A1_avg;
        eventSec(e).A2data = A2_sec;
        eventSec(e).A2avg = A2_avg;
        eventSec(e).B1data = B1_sec;
        eventSec(e).B1avg = B1_avg;
        eventSec(e).B2data = B2_sec;
        eventSec(e).B2avg = B2_avg;
        e=e+1;
        endOfLast = endTime;
    end
end
%}
%{
%% Plot sections
f2 = figure('Position',pos);
f2.NumberTitle = 'off';
numPlots = size(eventSec);
numPlots = numPlots(2);
for i=1:numPlots
    clear xlabel ylabel;
    subplot(1,numPlots,i);
    hold on;
    ax = gca;
    xlabel('Time (s)')
    ylabel('Flow (SCCM)')
    
    A1data = eventSec(i).A1data;
    A2data = eventSec(i).A2data;
    B1data = eventSec(i).B1data;
    B2data = eventSec(i).B2data;
    PID_data = eventSec(i).PIDdata;
    xmin = min(PID_data(:,1));
    xmax = max(PID_data(:,1));
    ax.XLim = [xmin xmax];
    ax.YLim = [-5 110];
    
    % plot olfa shit
    plot(A1data,'DisplayName','A1 flow');
    plot(A2data,'DisplayName','A2 flow');
    plot(B1data,'DisplayName','B1 flow');
    plot(B2data,'DisplayName','B2 flow');
    
    % plot pid
    yyaxis right
    plot(PID_data,'DisplayName','PID');
    %ylabel('PID value (mV)');
    ax.YLim = [ymin ymax];
    
    hold off;
end
%}
