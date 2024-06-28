from flask import Flask, render_template, request
import requests
import logging
import logging.handlers
import configparser

app = Flask(__name__, template_folder='templates')

# Create a logger instance
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
# Set the log message format
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S %Z')

# Create a file handler and set the log file path
file_handler = logging.handlers.TimedRotatingFileHandler('smrr.log',
                                               when='midnight', interval=1, backupCount=2)

# Set the formatter for the file handler
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
config = configparser.ConfigParser()
configfile=f"config.properties"
config.read(configfile)

if(config.get("LOGGING","DEBUG")=='True'):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
	
# Replace 'YOUR_SOCIAL_SEARCHER_API_KEY' with your actual API key
SOCIAL_SEARCHER_API_KEY1 = config.get("API","API_AUTH")

bssHigh1Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_HIGH1")
bssHigh2Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_HIGH2")
bssMed1Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_MED1")
bssMed2Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_MED2")
bssLow1Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_LOW1")
bssLow2Inten = config.get("THRESHOLD_RANGE","BSS_INTEN_LOW2")

etsHigh1Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_HIGH1")
etsHigh2Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_HIGH2")
etsMed1Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_MED1")
etsMed2Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_MED2")
etsLow1Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_LOW1")
etsLow2Inten = config.get("THRESHOLD_RANGE","ETS_INTEN_LOW2")

aasHigh1Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_HIGH1")
aasHigh2Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_HIGH2")
aasMed1Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_MED1")
aasMed2Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_MED2")
aasLow1Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_LOW1")
aasLow2Inten = config.get("THRESHOLD_RANGE","AAS_INTEN_LOW2")

SOCIAL_SEARCHER_API_URL = 'http://api.social-searcher.com/v2/search'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    print(query)
    logger.info('social media brand keyword: '+str(query))
    trainedEmp = request.form.get('trainedScore')
    print(trainedEmp)

    untrainedEmp = request.form.get('untrainedScore')
    print(untrainedEmp)
    trainedScore = (int(trainedEmp)/(int(trainedEmp)+int(untrainedEmp)))*10
    untrainedScore = (int(untrainedEmp)/(int(trainedEmp)+int(untrainedEmp)))*10
    logger.info('untrained score: '+str(untrainedScore))
    logger.info('trained score: '+str(trainedScore))
    daysAudit = request.form.get('daysAudit')
    print(daysAudit)
    logger.info('Days of Audit: '+str(daysAudit))
    # Make a request to Social Searcher API
    headers = {'Api-Key': SOCIAL_SEARCHER_API_KEY1}
    params = {'q': query ,'limit':'100' ,'network':'all' ,'lang':'en'}
    response = requests.get(SOCIAL_SEARCHER_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('posts', [])
        #print(results)
        output = {'bssIntensity':'High' ,'etsIntensity':'High' ,'aasIntensity':'High', 'bssProb':'High' ,'etsProb':'High' ,'aasProb':'High', 'bssRecommAction':'Monitor social media' ,'etsRecommAction':'Schedule training session' ,'aasRecommAction':'Schedule next audit', 'bssCounts':'positive:0 negative:0 neutral:0' ,'smrrAverage':3.5}
        sentiment_counts = {'positive':0 ,'negative':0 ,'neutral':0}
        for post in results:
            senti = post.get('sentiment', '')
            # Classify sentiment
            if senti == "positive":
                sentiment_counts['positive'] += 1
            elif senti == "negative":
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1
        print(sentiment_counts)
        output['bssCounts'] = 'Positive: '+str(sentiment_counts['positive'])+', Neutral: '+str(sentiment_counts['neutral'])+', Negative: '+str(sentiment_counts['negative'])
        bsScore = int(int(sentiment_counts['positive']) + int(sentiment_counts['neutral']))/10
        logger.info('sentiment score: '+str(bsScore))
        aaScore = max(10 - int(daysAudit), 0) if int(daysAudit) < 10 else 0
        logger.info('Account Audit score: '+str(aaScore))		
        
        if int(bssHigh1Inten) <= int(bsScore) <= int(bssHigh2Inten):
            output['bssIntensity'] = 'High'
        elif int(bssMed1Inten) <= int(bsScore) <= int(bssMed2Inten):
            output['bssIntensity'] = 'Medium'
        elif int(bssLow1Inten) <= int(bsScore) <= int(bssLow2Inten):
            output['bssIntensity'] = 'Low'
        else:
            output['bssIntensity'] = 'Error'
			
        if int(etsHigh1Inten) <= int(trainedScore) <= int(etsHigh2Inten):
            output['etsIntensity'] = 'High'
        elif int(etsMed1Inten) <= int(trainedScore) <= int(etsMed2Inten):
            output['etsIntensity'] = 'Medium'
        elif int(etsLow1Inten) <= int(trainedScore) <= int(etsLow2Inten):
            output['etsIntensity'] = 'Low'
        else:
            output['etsIntensity'] = 'Error'

        if int(aasHigh1Inten) <= int(aaScore) <= int(aasHigh2Inten):
            output['aasIntensity'] = 'High'
        elif int(aasMed1Inten) <= int(aaScore) <= int(aasMed2Inten):
            output['aasIntensity'] = 'Medium'
        elif int(aasLow1Inten) <= int(aaScore) <= int(aasLow2Inten):
            output['aasIntensity'] = 'Low'
        else:
            output['aasIntensity'] = 'Error'

        output['etsProb'] = output['etsIntensity']
        output['aasProb'] = output['aasIntensity']
        output['bssProb'] = getBssProbability(output['etsProb'], output['aasProb'])
        output['bssRecommAction'] = getBssRecomm(output['bssIntensity'], output['bssProb'])
        
        if output['etsProb'] == 'Low':
            output['etsRecommAction'] = config.get("RECOMM_TEXT","ETS_LOW_LOW")
        elif output['etsProb'] == 'Medium':
            output['etsRecommAction'] = config.get("RECOMM_TEXT","ETS_MED_MED")
        elif output['etsProb'] == 'High':
            output['etsRecommAction'] = config.get("RECOMM_TEXT","ETS_HIGH_HIGH")
        else:
            output['etsRecommAction'] = 'Error'
			
        if output['aasProb'] == 'Low':
            output['aasRecommAction'] = config.get("RECOMM_TEXT","AAS_LOW_LOW")
        elif output['aasProb'] == 'Medium':
            output['aasRecommAction'] = config.get("RECOMM_TEXT","AAS_MED_MED")
        elif output['aasProb'] == 'High':
            output['aasRecommAction'] = config.get("RECOMM_TEXT","AAS_HIGH_HIGH")
        else:
            output['aasRecommAction'] = 'Error'
        #logger.info('BSS ratio = '+str(bsScore)+':'+str(sentiment_counts['negative']))
        #logger.info('ETS ratio = '+str(trainedScore)+':'+str(untrainedScore))
        smrrScore = overallScore(int(bsScore), int(trainedScore), int(aaScore))
        logger.info('SMRR score: '+str(smrrScore))				
        output['smrrAverage'] = smrrScore
        #return render_template('search_results.html', query=query, results=results, sentiment_counts=sentiment_counts)
        return render_template('search_output.html', query=query, output=output)
    else:
        return f"Error fetching search results: {response.text}"

def getBssProbability(etsProb, aasProb):
    if etsProb == 'Low':
        if aasProb == 'Low':
            return 'Low'
        elif aasProb == 'Medium':
            return 'Medium'
        elif aasProb == 'High':
            return 'High'
        else:
            return 'Error'
    elif etsProb == 'Medium':
        if aasProb == 'Low':
            return 'Medium'
        elif aasProb == 'Medium':
            return 'Medium'
        elif aasProb == 'High':
            return 'High'
        else:
            return 'Error'
    elif etsProb == 'High':
        if aasProb == 'Low':
            return 'High'
        elif aasProb == 'Medium':
            return 'High'
        elif aasProb == 'High':
            return 'High'
        else:
            return 'Error'
    else:
        return 'Error'
	
def getBssRecomm(bssIntensity, bssProb):
    if bssIntensity == 'Low':
        if bssProb == 'Low':
            return config.get("RECOMM_TEXT","BSS_LOW_LOW")
        elif bssProb == 'Medium':
            return config.get("RECOMM_TEXT","BSS_LOW_MED")
        elif bssProb == 'High':
            return config.get("RECOMM_TEXT","BSS_LOW_HIGH")
        else:
            return 'Error'
    elif bssIntensity == 'Medium':
        if bssProb == 'Low':
            return config.get("RECOMM_TEXT","BSS_MED_LOW")
        elif bssProb == 'Medium':
            return config.get("RECOMM_TEXT","BSS_MED_MED")
        elif bssProb == 'High':
            return config.get("RECOMM_TEXT","BSS_MED_HIGH")
        else:
            return 'Error'
    elif bssIntensity == 'High':
        if bssProb == 'Low':
            return config.get("RECOMM_TEXT","BSS_HIGH_LOW")
        elif bssProb == 'Medium':
            return config.get("RECOMM_TEXT","BSS_HIGH_MED")
        elif bssProb == 'High':
            return config.get("RECOMM_TEXT","BSS_HIGH_HIGH")
        else:
            return 'Error'
    else:
        return 'Error'

def overallScore(score_a, score_b, score_c):
    # Define the weights for each score
    weight_a = 0.6
    weight_b = 0.2
    weight_c = 0.2

    # Calculate the weighted average
    weighted_average = (score_a * weight_a) + (score_b * weight_b) + (score_c * weight_c)

    return round(weighted_average, 2)

if __name__ == '__main__':
    app.run(debug=False)
