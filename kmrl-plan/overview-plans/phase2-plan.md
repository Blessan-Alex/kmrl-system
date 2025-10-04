First is the connectors

Gmail, Google Drive right now for prototype

But actually problem statement asks for Maximo , Sharepoint , Whatsapp Business, Email, Adhoc cloud links, Manual Uploads

Have two scripts that connect with Gmail and google drive , get the credentials, jsons, id everything. Make sure we authenticate it right(always a headache, make sure tokens need to be refreshed everytime or it expires)

At first sync it should take the historical data, if there is too many historical data then 
handle it by taking only 50 previous from time , then keep doing that whenever there is free 
resource . 
At the same time incremental sync should happen, if we upload on the go to google drive, we should be able to get it in the next sync, same goes if someone sends an email with attachements.

We need to find ways to handle adhoc cloud links, if it is dropped in the chat. Also whatsap token generation is having some issues with OTP

Decide on the timeline for the sync, how often , for now a small time (testing/hackathon purposes). But also have a production grade number in mind

Make sure that we can follow the same pattern to add more connectors to this so that in the future we can integrate the maximo and sharepoint and whatever. Follow clean architecture principles

Do keep in mind that we are going to make this an airflow workflow. And for connectors whatever we need should be added , Research on whether we need a queue system or celery.

Documet processing pipeline

From the queue worker picks up the file , how does it pick it up based on what ? 
then we need to classify based on file types 

   ├── Technical drawings (.dwg, .dxf, .step, .stp, .iges, .igs)
   ├── Images (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .tif, .webp) ocr - tesseract
   ├── PDFs (text, image, or mixed content) 
   ├── Office documents (.docx, .doc, .xlsx, .xls, .pptx, .ppt) - markitdown
   ├── Text files (.txt, .md, .rst, .html, .xml, .json, .csv) 
   └── Unknown files
All these file types are there , so wee need to send all technical drawings to one route where the technical drawing processing will take place (convert all them to dxf using a library , then extract using a library )

Images we have to use ocr for thsi , should i use docling or tesseract , we need to handle bilingual as well. is maltesseract and normal teeessarct the same library or different , docling doesnt handle malayalam well, have to test out leka ocr as well
how do we handle the image enhancement ? if the quality is poor we need to send it to image enhancement or do we need to enhance it everytime nad then do ocr , what is the threshold to do enahcenevemt ? maybe we could have a quality test assessment and then decide 
How do we make sure that whatever we got is good enough for the later parts and shouldnt be rejected
If image is poor uality or couldnt do anything , then we should send the image to humamn review. is there anything else we can think about in image 
if images have a table image , how do we extract it and store ?

pdfs - could have text only , then markitdown , could have images + text , markitdown plus ocr or do we send it to mixed processing ? , could have tables , fianncail docs , etc , how do we handle that , check for all cases to handle pdf , pytopdf ? or docling ?
what to do about language , english /malaylam , what if it is mixed , do these library extract it properly ? 

office documents , same thing , bilingual handling , how to detect , how to extract ? markitdown ? 

text files , markitdown ? or docling ? if theres large data , datasets of csv will it succeslly extract everythign 

will unknwon files come down the pipeline ? if then human review do we neeed this ?


Make sure that this is also a workflow in airflow , and then what is next after extracting everythign ? do we need to add anything in postgress ? store these extracted ? next is data preprocessing and rag piepile , lets not focus on that but make sure documetn processing is ready for that next
what data is given to next pipeline , is there some schema to be followed or added ? 