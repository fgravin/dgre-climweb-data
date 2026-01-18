#library(raster)
#1. Configurer les repertoires par defaut
models<-c("World-Wide HYPE v1.3.5", 
          "Niger HYPE v2.30", 
          "Niger HYPE v2.30 + Updating with local stations",
          "West-Africa HYPE v1.2",
          "West-Africa HYPE v1.2 + Updating with local stations",
          "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU")

directories<-c("wa-hype1.3_hgfd3.2_ecoper_noEOWL_noINSITU",
               "niger-hype2.30_hgfd3.2_ecoper_noEOWL_noINSITU",
               "niger-hype2.30_hgfd3.2_ecoper_noEOWL_INSITU-AR",
               "wa-hype1.2_hgfd3.2_ecoper_noEOWL_noINSITU",
               "wa-hype1.2_hgfd3.2_ecoper_noEOWL_INSITU-AR",
               "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU")
#for (i in 2:2) {
for (i in 2:length(models)) {
  name.out<-paste("/var/www/tethys/workspaces/sapci_bfa/app_workspace",
                  directories[i], "static/thresholds-rp-cout.txt", sep="/")
  name.retlev<-name.out
  fileDir<-paste("/var/www/tethys/workspaces/sapci_bfa/app_workspace",
                 directories[i], sep="/")
  name.wl.txt<-"004_mapWarningLevel.txt"
  shp.dir<-paste("/var/www/tethys/workspaces/sapci_bfa/app_workspace",
                 directories[i], "static", sep="/")
  shp.name<-"subbasins"
  wl_dir<-paste("/var/www/tethys/workspaces/sapci_bfa/app_workspace",
                directories[i], "wl", sep="/")
  
  #1. Mettre a jour les previsions
  source("/root/scripts/Calcul_return_period_ecowas.R")
  #date=paste0(substr(Sys.Date(), 1,4), substr(Sys.Date(), 6,7),substr(Sys.Date(), 9,10))
  date=Sys.Date()
  #script_name="C:/Users/minou/OneDrive/Documents/AGRHYMET_CRA/FANFAR/Automatisation_visualisation/download_forecast/download_forecast_all.py"
  #download_exe<-paste("python ", script_name, "-m ", i, " -d ", Sys.Date(), sep=" ")
  #system(download_exe)
  system(paste0("python3 /root/scripts/download_forecast/download_forecast", i, ".py"))
  #2. Formater colorscales, hindcast et forecast pour Tethys
  all_files<-dir(fileDir)
  forecast_files<-all_files[grep("forecast_timeCOUT", all_files)]
  #hindcast_files<-all_files[grep("hindcast_timeCOUT", all_files)]
  issue_dates<-as.Date(paste(substr(forecast_files, 2, 5), 
                             substr(forecast_files, 6, 7), 
                             substr(forecast_files, 8, 9), sep="-"))
  issue_date<-issue_dates[which.max(issue_dates)[length(which.max(issue_dates))]]
  
  
  last_wl_files<-dir(wl_dir, pattern=".txt")
  last_issue_date<-max(as.Date(substr(last_wl_files, 21, 31)))
  
  if(issue_date>=last_issue_date) {
    forecast_file<-forecast_files[which.max(issue_dates)[length(which.max(issue_dates))]]
    hindcast_file<-all_files[grep(paste0(substr(issue_date, 1,4),substr(issue_date, 6,7),substr(issue_date, 9,10),
                                         "_hindcast_timeCOUT"), all_files)]
    
    forecast_data<-ReadTimeOutput(paste(fileDir, forecast_file, sep="/"))
    forecast_data<-t(forecast_data)
    colnames(forecast_data)<-forecast_data[1,]
    forecast_data<-forecast_data[-1,]
    forecast_data<-cbind(sub("X", "", rownames(forecast_data)), forecast_data)
    forecast_data<-cbind(c(1:nrow(forecast_data)),forecast_data)
    colnames(forecast_data)[1:2]<-c("index", "SUBID")
    write.table(forecast_data, paste(wl_dir,  "forecast.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    
    
    hindcast_data<-ReadTimeOutput(paste(fileDir, hindcast_file, sep="/"))
    hindcast_data<-t(hindcast_data)
    colnames(hindcast_data)<-hindcast_data[1,]
    hindcast_data<-hindcast_data[-1,]
    hindcast_data<-cbind(sub("X", "", rownames(hindcast_data)), hindcast_data)
    hindcast_data<-cbind(c(1:nrow(hindcast_data)),hindcast_data)
    colnames(hindcast_data)[1:2]<-c("index", "SUBID")
    write.table(hindcast_data, paste(wl_dir, "hindcast.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    
    #Preparation du fichier colorscales
    retlev<-read.table(name.retlev,header=T)
    retlev2<-t(retlev[,-1])
    colnames(retlev2)<-retlev[,"SUBID"];rm(retlev)
    # retlev2[,1:5]
    wl.rp<-as.numeric(sub("RP","",rownames(retlev2)))
    # Define function to check wich warning level we should assign
    # Note the principle here is to check for the highest warning level during the entire forecast period (all days)
    # If no return level value is present there is never a warning issued
    wldef<-function(subid) {  
      #subid<-"816"
      myf<-thisq1[,subid]
      mywl<-0
      if(!any(is.na(retlev2[,subid]))) {  # ignoring if the return levels could not be estimated, then never warn
        for(k in 1:length(wl.rp)) { #k<-1
          if(any(myf>retlev2[k,subid])) {mywl<-k}
        }}
      return(mywl)
    }
    
    # Derive warning levels for the current forecast and save output
    thisq<-ReadTimeOutput(paste(fileDir,forecast_file,sep="/"))
    
    # determine first and last date in file
    cdate=as.character(thisq[1,1],format="%Y-%m-%d")
    all_date<-thisq[,1]
    #  edate=as.character(thisq[nrow(thisq),1],format="%Y%m%d")
    
    # continue
    colnames(thisq)<-sub("X","",colnames(thisq))
    thisq<-thisq[,-1]  # remove date column as we don't use it here
    
        #Ajouter une exception pour le Burkina
    if(i==6) {
      mmymatch=match(colnames(thisq),colnames(retlev2))
      retlev2<-retlev2[,mmymatch]
    }
    
    if(all(colnames(thisq)==colnames(retlev2))){ # check that the columns match
      thiswls<-NULL
      for (ii in 1:nrow(thisq)) {
        thisq1<-thisq[ii,]
        thiswl<-sapply(colnames(thisq1),FUN = wldef)
        thiswls<-cbind(thiswls,thiswl)
      }
      thiswl.df<-cbind(as.numeric(rownames(thiswls)), thiswls, apply(thiswls, 1, max, na.rm=T))
      #colnames(thiswl.df)<-c("SUBID", paste0("WarningLevel", c(1:10)), "WarningLevel_max")
      colnames(thiswl.df)<-c("SUBID", as.character(all_date), "WarningLevel_max")
      writeLines(text=paste(" Warning levels based on magnitudes with return-period:", paste(wl.rp,collapse=", "), "years"),
                 con=paste(wl_dir,paste0("004_mapWarningLevel_", issue_date, ".txt"),sep="/"))
      suppressWarnings(write.table(thiswl.df,
                                   file=paste(wl_dir,paste0("004_mapWarningLevel_", issue_date, ".txt"),sep="/"),append=T,row.names=F,quote=F,sep=","))
      #rm(thiswl,thiswl.df)
    }
    
    thiswl.df<-cbind(c(1:nrow(thiswl.df)), thiswl.df)
    colnames(thiswl.df)<-c("index", "SUBID", paste0("day", c(1:10)), "max")
    
    
    write.table(thiswl.df, paste(wl_dir, "colorscales.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    write.table(thiswl.df, paste(wl_dir, "colorscales1.csv", sep="/"),
                sep=",", row.names = F, quote=F)

    
    #Preparation du fichier forecast_dates
    
    forecast_date<-data.frame(Jour=c( paste0("day", c(1:10)), "max"), 
                              Date=c(substr(all_date, 1, 10),"Max of 10 days forecast"))
    
    write.table(forecast_date, paste(wl_dir, "forecast_dates.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    if (i==6) {
        wl_dir1<-paste("/var/www/tethys/workspaces/sapci_bfa/app_workspace",
                "riverine_flood", "wl", sep="/")
    thiswl.df=rbind(thiswl.df, rep(0, ncol(thiswl.df)))
    write.table(thiswl.df, paste(wl_dir1, "colorscales.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    write.table(thiswl.df, paste(wl_dir1, "colorscales1.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    write.table(forecast_date, paste(wl_dir1, "forecast_dates.csv", sep="/"),
                sep=",", row.names = F, quote=F)
    }
  }
  
}






