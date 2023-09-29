data <- read.csv('processed_data.csv')
boxplot(data$lstn_Jun)
boxplot(data$tomato_production.tonnes.acre.)
title(main = "LSTN June")
min(data$tomato_farmland_area.acres.)


barplot(table(pdata$CA_county_ansi), ylim = c(0, 11))
title(main = "CA county frequency")
summary(pdata$tomato_production.tonnes.acre.)

library(rpart)
library(dplyr)
library(caTools)
library(party)

pdata <- read.csv('processed_data_without_outliers.csv')
for (i in 4:17) {
  pdata[,i] <- (pdata[,i] - mean(pdata[,i])) / sd(pdata[,i])
}
train_index <- sample(nrow(pdata), 0.5 * nrow(pdata))
train <- pdata[train_index, ]
test <- pdata[-train_index, ]

mod1 <- lm(train$tomato_production.tonnes.acre. ~ train$lstd_Jun + train$lstd_Jul
           + train$lstn_Jun + train$lstn_Jul
           + train$gpm_Jun + train$gpm_Jul + train$ndvi_Jun + train$ndvi_Jul + train$ET)
mod2 <- lm(train$tomato_production.tonnes.acre. ~ train$lstd_Jun + train$lstd_Jul
           + train$lstd_Aug + train$lstn_Jun + train$lstn_Jul + train$lstn_Aug
           + train$gpm_Jun + train$gpm_Jul + train$gpm_Aug + train$ndvi_Jun + train$ndvi_Jul 
           + train$ndvi_Aug + train$ET)
pred <- predict(mod1, test)
t.test(pred, test$tomato_production.tonnes.acre., var.equal = TRUE)
pred2 <- predict(mod2, test)
t.test(pred2, test$tomato_production.tonnes.acre., var.equal = TRUE)

mod1
mod2
