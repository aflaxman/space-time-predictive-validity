**********************
* Description: 
* Create a csv with the male 45q15 estimates from Rajaratnam et. al. 2010 to be used as the gold standard in a simulation study
* Author: 
* Jake Marcus
********************** 

* Prepare the country codes file for merging
use "J:\Usable\Common Indicators\Country Codes\countrycodes_official.dta", clear
keep countryname_ihme iso3
sort countryname_ihme
tempfile codes
save `codes', replace

* Read in the gold standard 45q15s
insheet using "J:\project\models\space-time-predictive-validity\space-time-predictive-validity\45q15m.csv", clear
rename country countryname_ihme
sort countryname_ihme
merge countryname_ihme using `codes'
keep if _merge == 3
keep iso3 year v45q15_male
sort iso3 year
tempfile data
save `data', replace

* Prepare a dataset with all iso3s and a row for each year
use "J:\Usable\Common Indicators\Country Codes\countrycodes_official.dta", clear
keep if ihme_country == 1 & ihme_std_name_2009 == 1
keep iso3 countryname_ihme gbd_region gbd_super_region

tempfile base
save `base', replace

g sex = "male"

save `base', replace

g year = .
forvalues y = 1970/2010 {
	replace year = `y' if year == .
	append using `base'
}
drop if year == .

sort iso3 year
merge iso3 year using `data'
drop _merge

rename v45q15_male y
replace y = y/1000

g age = ""

order iso3 countryname_ihme gbd_region gbd_super_region sex age year y

sort iso3 sex age year

outsheet using "J:\project\models\space-time-predictive-validity\space-time-predictive-validity\gold_45q15m.csv", replace comma
